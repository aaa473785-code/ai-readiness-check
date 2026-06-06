# AI活用度セルフチェックツール

DX推進担当・情シス向け｜自社のAI活用レベルを診断し、改善提案とコスト概算を出すツール（PoC）

## セットアップ

```powershell
# フォルダ作成・移動
mkdir C:\dev\ai-readiness-check
cd C:\dev\ai-readiness-check

# ファイルを配置（ai_readiness_check.py, requirements_check.txt）

# 仮想環境
python -m venv venv
venv\Scripts\Activate.ps1

# パッケージインストール
pip install -r requirements_check.txt
```

## 起動

```powershell
streamlit run ai_readiness_check.py
```

## API ON/OFF

- **OFF（デフォルト）**: 定型の診断コメントが表示される。APIキー不要
- **ON**: サイドバーでトグルをONにし、APIキーを入力。Claudeが回答内容を読んで個別の改善提案を生成

APIキーを環境変数に設定済みなら自動で読み込む:
```powershell
$env:ANTHROPIC_API_KEY = "sk-ant-..."
```

## 技術構成

- Python + Streamlit
- matplotlib（レーダーチャート）
- Anthropic API / Claude Haiku（ON/OFF切替）
