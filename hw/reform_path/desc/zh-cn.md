![Python Logo 图片](hw://img/python-logo.png)

（下载图片：[hw://img/python-logo.png](hw://img/python-logo.png)）

完成附件 path.py 中的函数 <code>reform_path</code>，使之对输入 <code>path</code> 产生输出满足：

*   所有输入中的 "\" 被当做 "/" 加以处理，且在输出中被转换为 "/"。
*   连续多个 "/" 被压缩成一个。
*   输入中的 "." 被直接删除。
*   输入中的 ".." 会导致一个父目录被删去。然而如果输入中已经不存在父目录，则抛出 ValueError 异常。
*   如果输入为空，或者所有父目录被删去，则根据下面的规则输出 "" 或者 "/"。
*   当且仅当输入以 "/" 开始时，输出才以 "/" 开始。
*   无论输入是否以 "/" 结尾，输出的结尾不带有 "/"，除非输出是 "/"。

该作业一共有 6 个测试点。此外，上交的代码必须符合相应语言的代码规范。请务必在截止日期前上交作业，否则不予计分。

```python
def reform_path(path):
    """Re-format the input `path`. Strip all "." and ".." parts. Return the
    new path that matches the following rules:

    *   All "\\" in old path should be treated as and translated to "/".
    *   Continous "/" should be compressed to one.
    *   "." in old path should be stripped directly.
    *   ".." in old path should consume one parent dir. However if no parent
        exists, a `ValueError` should be raised.
    *   If old path is empty, or all parents in old path is consumed, new path
        should be "" or "/", depending on the following rule.
    *   New path should starts with "/" if and only if the old does.
    *   Whether or not the old path ends with "/", new path shouldn't, unless
        it is "/".
    """

    raise NotImplementedError()
```
