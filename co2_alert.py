#!/usr/bin/env python3

from ambient import Ambient
import json
import subprocess
import time
import logging
import logging.handlers
import os
from datetime import datetime

# ログ設定
try:
    # syslogハンドラーを使用してシステムログに出力
    syslog_handler = logging.handlers.SysLogHandler(address='/dev/log', facility=logging.handlers.SysLogHandler.LOG_LOCAL0)
    syslog_handler.setFormatter(logging.Formatter('co2_alert: %(levelname)s - %(message)s'))

    # コンソール出力用ハンドラー
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

    # ロガーの設定
    logger = logging.getLogger("CO2Alert")
    logger.setLevel(logging.INFO)
    logger.addHandler(syslog_handler)
    logger.addHandler(console_handler)
    
except Exception as e:
    # syslogに接続できない場合は標準出力のみに出力
    print(f"システムログへの接続に失敗しました: {str(e)}")
    print("標準出力のみにログを出力します")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )
    logger = logging.getLogger("CO2Alert")

# 設定パラメータ
# Ambient設定
AMBIENT_CHANNEL_ID = ""  # ここにあなたのAmbientのチャネルIDを設定
AMBIENT_WRITE_KEY = ""   # ここにあなたのAmbientのライトキーを設定
AMBIENT_READ_KEY = ""    # ここにあなたのAmbientのリードキーを設定

# アラート閾値
CO2_THRESHOLD = 1000.0  # CO2閾値（ppm）

# Alexa設定
ALEXA_DEVICE_NAME = "リビングルーム"  # Alexaデバイス名を設定（例：リビングルーム）
ALEXA_CONTROL_PATH = "/path/to/alexa-remote-control.sh"  # alexa-remote-control.shのフルパス

# アラート間隔（秒）- 同じアラートを繰り返し送信しないための間隔
ALERT_INTERVAL = 1800  # 30分（秒単位）

# 最後のアラート時間を保存するファイルパス
LAST_ALERT_TIME_FILE = "/tmp/co2_alert_last_time.txt"

def get_ambient_data():
    """
    Ambientからデータを取得する関数（ambient-python-libを使用）
    """
    try:
        # 設定値の検証
        if not AMBIENT_CHANNEL_ID or not AMBIENT_READ_KEY:
            logger.error("AmbientのチャネルIDまたはリードキーが設定されていません")
            return None
            
        # ambient-python-libを使用してデータを取得
        ambient = Ambient(AMBIENT_CHANNEL_ID, AMBIENT_WRITE_KEY, AMBIENT_READ_KEY)
        data = ambient.read(n=1)  # 最新の1件のデータを取得
        
        if data and len(data) > 0:
            co2 = data[0].get('d3')  # d3がCO2濃度
            
            # 数値であることを確認
            if co2 is None:
                logger.error("AmbientからのデータでCO2濃度が取得できませんでした")
                return None
                
            return float(co2)
        else:
            logger.error("Ambientからのデータが空です")
    except Exception as e:
        logger.error(f"データ取得中にエラーが発生しました: {str(e)}")
    
    return None

def send_alexa_alert(co2):
    """
    Alexaでアラートを発話する関数
    """
    current_time = time.time()
    last_alert_time = get_last_alert_time()
    
    # 前回のアラートから設定時間以上経過しているか確認
    if current_time - last_alert_time < ALERT_INTERVAL:
        logger.info(f"前回のアラートから{ALERT_INTERVAL/60}分経過していないため、アラートをスキップします")
        last_time_str = datetime.fromtimestamp(last_alert_time).strftime('%Y-%m-%d %H:%M:%S')
        next_time_str = datetime.fromtimestamp(last_alert_time + ALERT_INTERVAL).strftime('%Y-%m-%d %H:%M:%S')
        logger.info(f"前回: {last_time_str}, 次回可能時間: {next_time_str}")
        return
    
    try:
        # alexa-remote-controlコマンドを使用してAlexaに発話させる
        message = f"二酸化炭素濃度が{int(co2)}ppmに達しています。換気してください。"
        command = f'"{ALEXA_CONTROL_PATH}" -d "{ALEXA_DEVICE_NAME}" -e speak:"{message}"'
        
        logger.info(f"Alexaコマンドを実行: {command}")
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("Alexaアラートの送信に成功しました")
            # アラート送信時間を保存
            save_last_alert_time(current_time)
        else:
            logger.error(f"Alexaアラートの送信に失敗しました: {result.stderr}")
    
    except Exception as e:
        logger.error(f"Alexaアラート送信中にエラーが発生しました: {str(e)}")

def check_and_alert():
    """
    CO2濃度を確認し、閾値を超えていればアラートを送信
    """
    co2 = get_ambient_data()
    
    if co2 is None:
        logger.warning("CO2濃度データが取得できませんでした")
        return
    
    logger.info(f"取得したデータ - CO2濃度: {co2}ppm")
    
    # 閾値を超えているか確認
    if co2 >= CO2_THRESHOLD:
        logger.info(f"閾値を超えました - CO2濃度: {co2}ppm (閾値: {CO2_THRESHOLD}ppm)")
        send_alexa_alert(co2)
    else:
        logger.info("閾値以下のため、アラートは送信しません")

def get_last_alert_time():
    """
    前回アラートを送信した時間を取得する関数
    """
    try:
        if os.path.exists(LAST_ALERT_TIME_FILE):
            with open(LAST_ALERT_TIME_FILE, 'r') as f:
                return float(f.read().strip())
        return 0
    except Exception as e:
        logger.error(f"前回のアラート時間の読み込みに失敗しました: {str(e)}")
        return 0

def save_last_alert_time(timestamp):
    """
    アラートを送信した時間を保存する関数
    """
    try:
        with open(LAST_ALERT_TIME_FILE, 'w') as f:
            f.write(str(timestamp))
        logger.info(f"アラート時間を保存しました: {datetime.fromtimestamp(timestamp)}")
    except Exception as e:
        logger.error(f"アラート時間の保存に失敗しました: {str(e)}")

def main():
    """
    メイン関数
    """
    logger.info("CO2アラートプログラムを開始します")
    
    # 設定情報の確認
    if not AMBIENT_CHANNEL_ID or not AMBIENT_READ_KEY:
        logger.error("Ambient設定が不完全です。AMBIENT_CHANNEL_IDとAMBIENT_READ_KEYを設定してください。")
        return
    
    # 前回のアラート時間を確認
    last_time = get_last_alert_time()
    if last_time > 0:
        last_time_str = datetime.fromtimestamp(last_time).strftime('%Y-%m-%d %H:%M:%S')
        logger.info(f"前回のアラート時間: {last_time_str}")
    
    try:
        # 一回実行
        check_and_alert()
        logger.info("プログラムが正常に終了しました")
    except Exception as e:
        logger.error(f"予期せぬエラーが発生しました: {str(e)}")

if __name__ == "__main__":
    main()
