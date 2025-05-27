# CO2アラートシステム

このプログラムは、Ambientから二酸化炭素(CO2)濃度データを取得し、設定された閾値を超えた場合にAlexaを使って換気アラートを発話します。

## 必要条件

- Python 3.6以上
- `ambient-python-lib`ライブラリ（GitHubリポジトリからインストール）
- `alexa-remote-control`が適切にセットアップされていること

## インストール方法

1. 必要なPythonパッケージをインストールします：

```bash
pip install git+https://github.com/AmbientDataInc/ambient-python-lib.git
```

2. `alexa-remote-control`をセットアップします（まだの場合）：

```bash
git clone https://github.com/thorsten-gehrig/alexa-remote-control.git
cd alexa-remote-control
# alexa-remote-controlのセットアップ手順に従ってセットアップを完了させてください
```

## 設定方法

`co2_alert.py`ファイルを開き、以下の設定パラメータを編集してください：

1. Ambient設定：
   ```python
   AMBIENT_CHANNEL_ID = "あなたのチャネルID"
   AMBIENT_WRITE_KEY = "あなたのライトキー"
   AMBIENT_READ_KEY = "あなたのリードキー"

   co2 = data[0].get('d3')  # データー3にCO2濃度を設定した場合はd3
   ```

2. Alexa設定：
   ```python
   ALEXA_DEVICE_NAME = "あなたのAlexaデバイス名"  # 例："リビングルーム"
   ALEXA_CONTROL_PATH = "/path/to/alexa-remote-control.sh"  # alexa-remote-control.shのフルパス
   ```

3. アラート閾値（必要に応じて変更）：
   ```python
   CO2_THRESHOLD = 1000.0  # CO2閾値（ppm）
   ```

4. アラート間隔（必要に応じて変更）：
   ```python
   ALERT_INTERVAL = 1800  # 30分（秒単位）
   ```

## 使用方法

プログラムを実行するには以下のコマンドを使用します：

```bash
python3 co2_alert.py
```

定期的に実行させたい場合は、cronを使用して設定することができます：

```bash
# 10分ごとに実行する例
crontab -e
```

そして以下の行を追加：

```
*/10 * * * * cd /home/あなたのパス/git/heatstroke_alert && python3 co2_alert.py
```

## ログ

プログラムの実行ログはシステムログ(`/var/log/syslog`または`/var/log/messages`)に出力されます。ログを確認するには次のコマンドを使用します：

```bash
# Ubuntuなどのシステムの場合
grep "co2_alert" /var/log/syslog

# CentOSなどのシステムの場合
grep "co2_alert" /var/log/messages
```

標準出力にも同時にログが表示されます。

## 注意点

- このプログラムは、設定した閾値（CO2濃度1000ppm以上）を超えた場合にのみアラートを発話します。
- 前回のアラートから設定時間（デフォルトは30分）経過するまで、新たなアラートは発話されません。
- 前回のアラート時間は `/tmp/co2_alert_last_time.txt` に保存されるため、システム再起動後はリセットされます。
- ログはシステムログに出力され、自動的にローテーションされます。
- cronで定期実行する場合でも、アラート間隔は適切に管理されます。

## システムログについて

- このプログラムはLinuxのシステムログ機能（syslog）を利用しています。
- システムによってログの場所は異なりますが、通常は `/var/log/syslog`（Debian系）または `/var/log/messages`（Red Hat系）に出力されます。
- システムログは通常、`logrotate`によって自動的にローテーションされ、肥大化を防止します。
- もしシステムログへのアクセス権限がない環境で実行すると、標準出力にのみログが出力されます。

## alexa-remote-controlについて

- このプログラムでは `alexa-remote-control.sh` スクリプトを使用します。
- 環境によってパスが異なるため、`ALEXA_CONTROL_PATH` 変数にフルパスを設定する必要があります。
- 例: `/home/username/alexa-remote-control/alexa-remote-control.sh`
- alexa-remote-controlが正しく設定されていないと、Alexaでのアナウンスが失敗します。

## トラブルシューティング

### エラー: "can only concatenate str (not "NoneType") to str"

このエラーは通常、次の原因で発生します：

1. **AMBIENT_CHANNEL_IDが未設定または不正**：
   - チャネルIDが正しく設定されていることを確認してください。
   - チャネルIDは数値である必要があります。

2. **AMBIENT_READ_KEYが未設定または不正**：
   - リードキーが正しく設定されていることを確認してください。

3. **Ambientサーバーへの接続エラー**：
   - インターネット接続が正常であることを確認してください。
   - AmbientのAPIサービスが利用可能であることを確認してください。

設定を修正する方法：

```bash
# 設定ファイルを編集
nano co2_alert.py

# 以下のパラメータを正しく設定
# AMBIENT_CHANNEL_ID = "12345"  # 実際のチャネルID（数字）
# AMBIENT_READ_KEY = "abcdef123456"    # 実際のリードキー
```

### エラー: "alexa-remote-control.sh: command not found"

このエラーはalexa-remote-controlのパスが正しく設定されていない場合に発生します：

1. alexa-remote-control.shのフルパスを確認：
   ```bash
   which alexa-remote-control.sh
   # または
   find / -name "alexa-remote-control.sh" 2>/dev/null
   ```

2. 見つかったパスで`ALEXA_CONTROL_PATH`を設定してください。
