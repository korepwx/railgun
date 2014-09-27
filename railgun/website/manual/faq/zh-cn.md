{%- extends "base.md" -%}
{%- block main -%}
# 常见问题

## 上传压缩包

### 我可以上传那些压缩包格式？

答：_zip, rar, tar, tgz, tar.gz, tbz, tar.bz2_。

### 我可以上传多大的压缩包？

答：_{{ max_upload | sizeformat }}_。

### 压缩包里可以有多少文件？

答：不多于 _{{ max_archive_file }}_ 个。

### 我可以同时提交多少作业？

答：每一个用户、每一个作业至多可以有 _{{ max_pending }}_ 个提交等待评测或正在运行。
{%- endblock %}