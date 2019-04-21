# GitHack script

### Usage

```bash
git clone https://github.com/hazzel-cn/GitHack.git
cd GitHack

// For githack.py, it collects all files classified by commits so that you can go through all files.
python3 githack.py http://you.target/.git/

// For gitclone.py, it clone the whole repository, which allows you to execute git commands.
python3 gitclone.py http://you.target/.git/
```

### Why this script

Without installing git, you can exploit a Git source code leak.

More details can be found in [https://www.hazzel.cn/2019/04/20/a-new-githack-script/](https://www.hazzel.cn/2019/04/20/a-new-githack-script/)