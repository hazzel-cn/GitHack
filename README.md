# GitHack Scripts

Scripts implementing Git Hack with recursion algorithm.

### Usage

```bash
git clone https://github.com/hazzel-cn/GitHack.git
cd GitHack

// For githack.py, it collects all files classified by commits so that you can go through all files.
python3 githack.py http://you.target/.git/

// For gitclone.py, it clones the whole repository, which allows you to execute git commands.
python3 gitclone.py http://you.target/.git/
```

### Screenshot

githack.py
![img](https://i0.wp.com/www.hazzel.cn/wp-content/uploads/2019/04/Screen-Shot-2019-04-21-at-11.44.49-PM.png?ssl=1)


gitclone.py
![img](https://i2.wp.com/www.hazzel.cn/wp-content/uploads/2019/04/Screen-Shot-2019-04-21-at-11.53.55-PM.png?ssl=1)

### Why this script

Without installing git, you can exploit a Git source code leak.

More details can be found in [https://www.hazzel.cn/2019/04/20/a-new-githack-script/](https://www.hazzel.cn/2019/04/20/a-new-githack-script/)


### Update log

2019-4-21 Improve recursion implementation (DFS) and fix some bugs.