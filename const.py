from enum import Enum


TEST = "test"
TOPIC_HELLO = ["こんにちは", "こん", "コン", "kon", "hello", "hi"]
PROJECT = "general-389304"
ZONE = "us-west1-b"
INSTANCE = "micra-server"
HELP = """
コマンド一覧：
# `/micra`
マイクラサーバー操作用のボタンを表示します。
`/micra`のあとに`start`、`stop`、`status`をつけることで直接サーバーの起動、停止、ステータスを確認できます。
(例：`/micra start` -> マイクラサーバーの起動)
# `@BOTti-chan`
BOTti-chanにメンションを送ることで、チャットGPTを使って会話することができます。
(今停止中)
"""


class VMStatus(Enum):
    """GCE VMのステータス:
    PROVISIONING: リソースが VM に割り当てられています。VM はまだ実行されていません。
    STAGING: リソースが確保され、最初の起動に向けて VM の準備が行われています。
    RUNNING: VM は起動され、実行中です。
    STOPPING: VM は停止中です。ユーザーが停止をリクエストしたか、エラーが発生しています。このステータスは一時的なもので、その後、VM は TERMINATED ステータスになります。
    REPAIRING: VM は修復中です。修復状態は、VM で内部エラーが発生した場合や、基盤のマシンが使用できない場合に発生します。この状態の VM は使用不能になります。修復に成功すると、VM は前述のいずれかの状態に戻ります。
    TERMINATED: VM は停止されました。ユーザーが VM を停止したか、VM で障害が発生しています。VM は再起動または削除できます。
    SUSPENDING: VM は一時停止中です。ユーザーが、VM を一時停止しました。
    SUSPENDED: VM は一時停止状態です。この VM は再開または削除できます。
    (https://cloud.google.com/compute/docs/instances/instance-life-cycle?hl=ja)
    """
    PROVISIONING = "provisioning"
    STAGING = "staging"
    RUNNING = "running"
    STOPPING = "stopping"
    REPAIRING = "repairing"
    TERMINATED = "terminated"
    SUSPENDING = "suspending"
    SUSPENDED = "suspended"
