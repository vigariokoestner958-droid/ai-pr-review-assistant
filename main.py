"""CLI entry point: python main.py <PR_URL> [--post] [--dry-run]"""
import os
import sys
import io
import click
from dotenv import load_dotenv

# Fix Windows GBK encoding for Unicode output
if sys.stdout.encoding and sys.stdout.encoding.lower() in ('gbk', 'cp936', 'gb2312'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

load_dotenv()


@click.command()
@click.argument("pr_url")
@click.option("--post/--dry-run", default=False,
              help="--post 将分析结果发布到 GitHub PR（默认 --dry-run 仅本地显示）")
def main(pr_url: str, post: bool):
    """AI PR Review 助手 — 输入 GitHub PR URL，获取 AI 代码审查。"""
    anthropic_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("AI_API_KEY")
    github_token  = os.getenv("GITHUB_TOKEN")

    if not anthropic_key:
        click.echo("❌ 缺少 ANTHROPIC_API_KEY，请在 .env 文件中配置", err=True)
        sys.exit(1)
    if not github_token:
        click.echo("❌ 缺少 GITHUB_TOKEN，请在 .env 文件中配置", err=True)
        sys.exit(1)

    from github_client import GitHubClient
    from analyzer import Analyzer
    from formatter import to_github_comment, print_cli

    # ── Step 1: Parse URL ──────────────────────────────────────────────────
    try:
        gh = GitHubClient(github_token)
        owner, repo, number = gh.parse_pr_url(pr_url)
    except ValueError as e:
        click.echo(f"❌ {e}", err=True)
        sys.exit(1)

    click.echo(f"🔍 正在获取 PR 数据：{owner}/{repo}#{number}...")

    # ── Step 2: Fetch PR ───────────────────────────────────────────────────
    try:
        pr = gh.get_pr(owner, repo, number)
    except Exception as e:
        click.echo(f"❌ 获取 PR 失败：{e}", err=True)
        sys.exit(1)

    click.echo(f"📄 PR：{pr.title}")
    click.echo(f"   变更：{pr.changed_files} 个文件，+{pr.additions}/-{pr.deletions} 行")
    click.echo("🤖 正在分析（Layer 1: 摘要...）")

    # ── Step 3: Analyze ────────────────────────────────────────────────────
    try:
        analyzer = Analyzer(anthropic_key)
        result = analyzer.analyze(pr)
    except Exception as e:
        click.echo(f"❌ 分析失败：{e}", err=True)
        sys.exit(1)

    click.echo("🧠 深度风险扫描完成")

    # ── Step 4: Display ────────────────────────────────────────────────────
    print_cli(pr, result)

    # ── Step 5: Post (optional) ────────────────────────────────────────────
    if post:
        click.echo("\n📤 正在发布到 GitHub...")
        comment_body = to_github_comment(pr, result)
        try:
            url = gh.post_comment(owner, repo, number, comment_body)
            click.echo(f"✅ 评论已发布：{url}")
        except Exception as e:
            click.echo(f"❌ 发布失败：{e}", err=True)
            sys.exit(1)
    else:
        click.echo("\n[dry-run 模式] 使用 --post 将结果发布到 GitHub PR")
        click.echo("\n─── GitHub 评论预览 ───")
        click.echo(to_github_comment(pr, result))


if __name__ == "__main__":
    main()
