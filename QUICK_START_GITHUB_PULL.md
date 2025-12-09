# GitHub 代码拉取 - 快速参考卡

## 🚀 3 步开始

### 1️⃣ 修改配置
```bash
nano pull_from_github.sh
# 修改: REPO_OWNER="your-username"
```

### 2️⃣ 上传脚本
```bash
scp pull_from_github.sh ubuntu@server-ip:/home/ubuntu/
```

### 3️⃣ 运行脚本
```bash
ssh ubuntu@server-ip
chmod +x pull_from_github.sh
./pull_from_github.sh
```

✅ **完成！** 代码已下载到 `/home/xinhua-tool`

---

## 📝 常用命令

```bash
# 首次克隆
./pull_from_github.sh

# 更新代码
./pull_from_github.sh

# 指定配置
./pull_from_github.sh <user> <repo> <dir> <branch>

# 查看代码
cd /home/xinhua-tool && ls -la

# 查看 Git 状态
cd /home/xinhua-tool && git status
```

---

## 🔧 三个版本

| 脚本 | 使用场景 |
|------|----------|
| `pull_from_github.sh` | ✅ 日常使用（推荐） |
| `pull_github_simple.sh` | 快速测试 |
| `pull_from_github_secure.sh` | ✅ 生产环境（推荐） |

---

## 🔐 Token 配置

**当前 Token**:
```
ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**安全存储（推荐）**:
```bash
echo 'export GITHUB_TOKEN="ghp_xxx"' > ~/.github_token
chmod 600 ~/.github_token
source ~/.github_token && ./pull_from_github_secure.sh
```

---

## ⚙️ 自动更新

```bash
# 添加定时任务（每天 2 点）
crontab -e

# 添加这一行：
0 2 * * * cd /home/ubuntu && ./pull_from_github.sh >> /var/log/github-pull.log 2>&1
```

---

## ❗ 常见问题

### 权限不足
```bash
sudo mkdir -p /home
sudo chown $USER:$USER /home
```

### Git 未安装
```bash
sudo apt-get update
sudo apt-get install -y git
```

### Token 失效
访问 https://github.com/settings/tokens 生成新 Token

---

## 📚 完整文档

- [GitHub拉取代码说明.md](GitHub拉取代码说明.md) - 中文详细指南
- [GITHUB_PULL_GUIDE.md](GITHUB_PULL_GUIDE.md) - 英文完整文档
- [GITHUB_PULL_SUMMARY.md](GITHUB_PULL_SUMMARY.md) - 功能总结

---

## ⚠️ 重要提示

1. **修改 REPO_OWNER** - 必须改为你的 GitHub 用户名
2. **保护 Token** - 不要泄露 Personal Access Token
3. **测试先行** - 先在测试环境验证
4. **定期备份** - 拉取前备份重要数据

---

**提示**: 如需帮助，运行 `./pull_from_github.sh` 查看提示信息

