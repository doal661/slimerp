# slimerp
Japanese erp made by my hobby.

 Iron Vault (v8.5 CRT Legacy Edition)
"Solid as Iron, Simple as Legacy."
A hyper-lightweight, standalone ERP solution tailored for Japanese SMEs to comply with the Electronic Book Storage Act and the Invoice System.
日本の電子帳簿保存法・インボイス制度に対応した、超軽量・スタンドアローン型ERPツール。
🇬🇧 English Description
📖 Overview
Iron Vault is a hobbyist project designed to solve a complex problem with extreme simplicity. It serves as a miniature ERP system for small manufacturing companies in Japan that need to manage ledgers and invoices without relying on expensive, cloud-based subscriptions.
Built with Python 3.4 (Standard Library only), it runs flawlessly on legacy hardware (even Windows XP) and modern systems alike.
✨ Key Features
Dual Database Architecture: Separate management for General Ledger (ERP) and Tax Invoices.
Japanese Invoice System Compliance: Fully supports "T-Numbers" (T-番号) and tax rate calculations (8% / 10%).
IME Input Guard: Automatic sanitization of Japanese IME input errors (e.g., converting full-width numbers/hyphens to half-width, handling Em dashes).
Tamper-Proofing: Generates a SHA-256 hash for every transaction to ensure data integrity.
CRT Optimized: UI designed for 1024x768 resolution.
Zero Dependencies: No pip install required. Uses only standard libraries.
🚀 How to Use & Deploy
Build: Compile main.py using PyInstaller on a Python 3.4 environment (Windows).
Deploy: Create a folder (e.g., IronVault_v8.5), place the generated .exe inside.
Run: Distribute the folder to the target PC. Place it on the desktop and run.
No installation wizard required. It's fully portable.
💾 Backup Strategy
The "Folder Copy" Method:
The database files (.db) are created inside the application folder.
To backup, simply copy and paste the entire folder to an external drive or cloud storage.
🇯🇵 日本語 (Japanese Description)
📖 概要
Iron Vault (アイアン・ボールト) は、中小規模の製造業や個人事業主向けに開発された、超軽量な経理・請求書管理ツールです。 高価なサブスクリプション型会計ソフトを使わずに、電子帳簿保存法およびインボイス制度への最低限の対応を可能にします。
Windows XP時代のレガシーPCでも動作するように設計されており、インストール不要でUSBメモリに入れて持ち運ぶことも可能です。
✨ 主な機能
インボイス制度完全対応: 適格請求書発行事業者の登録番号（T番号）の記録、軽減税率（8%・10%）の自動計算に対応。
強力な入力補正 (IME Guard): 全角数字、全角ハイフン、長音記号（ー）、漢数字などの入力ミスを自動で半角・正規フォーマットに修正します。
改ざん防止機能: 全取引データに対してSHA-256ハッシュ値を生成し、データの同一性を担保（簡易的な電子帳簿保存法要件への対応）。
CSVエクスポート: 税理士への提出用に、Excelで文字化けしない形式（UTF-8-SIG）でデータを出力可能。
レガシー環境最適化: 1024x768の解像度に最適化されており、古いCRTモニターでも快適に操作可能。
🚀 導入方法 (使い方)
本ソフトウェアは「ポータブル版」として設計されています。
配置: 配布されたフォルダを、デスクトップなどの好きな場所に置いてください。
起動: フォルダ内の exe ファイルを実行するだけで、すぐに使用可能です（インストール作業は不要です）。
運用: 日々の取引を入力し、「安全にさらに（COMMIT）」ボタンを押してください。
💾 バックアップについて
「フォルダごとコピー」してください:
データはすべてフォルダ内の .db ファイルに保存されます。
バックアップを取りたいときは、フォルダ全体をコピーして、USBメモリや外付けHDDに貼り付けてください。これだけで復元可能です。
🛠️ Technical Details (For Developers)
Language: Python 3.4.4
GUI Framework: Tkinter (Native Look & Feel)
Database: SQLite3
Build Tool: PyInstaller
Philosophy: "No pip, No cry." (Utilizes strictly Standard Libraries only for maximum compatibility).
⚠️ Disclaimer
This software is provided "as is", without warranty of any kind. While it is designed to assist with tax compliance, the user is responsible for verifying the accuracy of their financial records.
本ソフトウェアは趣味で制作されたものであり、法的な完全性を保証するものではありません。実務で使用される際は、必ず税理士等の専門家にご確認の上、利用者の責任においてご使用ください。
(c) 2026 AI Project. Created by a graduating CS student with a passion for retro-tech.



---

## ⚠️ Final Disclaimer (免責事項 / 면책 조항)

### 🇬🇧 English
**"Rigorous QA, AI-Assisted, Zero Liability."**
While I have performed extensive manual quality assurance and testing on the logic, a significant portion of the codebase was generated/optimized using AI. Therefore, I provide this software "as is" without any guarantees. By using this software, you acknowledge that the developer is **not responsible** for any financial, legal, or data-related consequences. Use it at your own risk.

### 🇯🇵 日本語
**「徹底した品質検数、AIによる補助、一切の責任否認」**
ロジックの品質検数は厳格に行っていますが、本ソフトウェアのコードはAIを活用して作成・最適化されています。したがって、本ツールの使用によって生じたいかなる損害（金銭的損失、法的トラブル、データ破損等）についても、開発者は**一切の責任を負いません**。あくまで「自己責任」でご利用ください。

### 🇰🇷 한국어
**"품질 검수는 철저히 마쳤으나, AI가 코딩한 결과물입니다."**
로직에 대한 품질 검수는 빡세게 진행했지만, 코드의 상당 부분이 AI를 통해 생성 및 최적화되었습니다. 따라서 본 소프트웨어의 사용으로 인해 발생하는 모든 법적, 경제적 책임은 **사용자 본인**에게 있으며, 개발자는 이에 대해 **어떤 책임도 지지 않습니다.** "내 알 바 아니니" 신중하게 판단하여 사용하십시오.
