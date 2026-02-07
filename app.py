
import os
import sys
import time
import tempfile
import whisper
import torch
import streamlit as st
from datetime import datetime
import pyperclip

# ページ設定
st.set_page_config(
    page_title="Whisper文字起こしツール",
    page_icon="�",
    layout="wide"
)

# Custom CSS for aesthetics
st.markdown("""
<style>
    /* 全体の背景色 */
    .stApp {
        background-color: #FFF0F5; /* Lavender Blush */
    }
    
    /* サイドバーの背景色 */
    [data-testid="stSidebar"] {
        background-color: #FFE4E1; /* Misty Rose */
    }

    /* テキストカラー */
    h1, h2, h3, .stMarkdown, p, li {
        color: #5D4037 !important; /* Soft Brown */
        font-family: 'Helvetica Neue', sans-serif;
    }

    /* メインボタンのデザイン */
    .stButton>button {
        color: #FFFFFF !important;
        background-color: #FFB7B2 !important; /* Pastel Pink */
        border: none;
        border-radius: 25px;
        height: 3.5em;
        width: 100%;
        font-weight: bold;
        font-size: 16px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 10px rgba(255, 183, 178, 0.4);
    }
    .stButton>button:hover {
        background-color: #FF9E9E !important;
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(255, 158, 158, 0.5);
    }
    
    /* ダウンロードボタンなどのセカンダリボタン */
    [kind="secondary"] {
        background-color: #FFFFFF !important;
        color: #FFB7B2 !important;
        border: 2px solid #FFB7B2 !important;
        border-radius: 25px;
    }

    /* ファイルアップローダー */
    [data-testid="stFileUploader"] section {
        background-color: #FFFFFF;
        border-radius: 20px;
        padding: 30px;
        border: 2px dashed #FFB7B2;
    }

    /* タイトル装飾 */
    h1 {
        text-align: center;
        padding-bottom: 20px;
        border-bottom: 3px dotted #FFB7B2;
        margin-bottom: 30px;
    }

    /* アラートやインフォメーション */
    .stAlert {
        background-color: #FFFFFF;
        border-radius: 15px;
        border: 1px solid #FFDAC1;
    }
    
    /* タブのデザイン */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #FFFFFF;
        border-radius: 20px 20px 0 0;
        color: #5D4037;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFF0F5;
        border-bottom: 2px solid #FFB7B2;
        color: #FFB7B2;
    }
</style>
""", unsafe_allow_html=True)

# キャッシュ設定（モデルを再ロードしないようにする）
@st.cache_resource
def load_whisper_model(model_name):
    """Whisperモデルをロードする（キャッシュ使用）"""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    return whisper.load_model(model_name, device=device)

def check_ffmpeg():
    """FFmpegがインストールされているか確認"""
    if os.system("ffmpeg -version > NUL 2>&1") != 0: # Windows uses NUL
        st.error("⚠️ FFmpegがインストールされていません。https://ffmpeg.org/download.html からダウンロードして、パスを通してください。")
        st.stop()

def get_available_models():
    """利用可能なWhisperモデルの一覧を返す"""
    return ["tiny", "base", "small", "medium", "large"]

def main():
    """メイン関数"""
    st.title("Whisper 文字起こしツール")
    st.markdown("""
    <div style='text-align: center; margin-bottom: 30px; color: #5D4037;'>
        音声・動画ファイルからテキストへの文字起こしを行います。<br>
        MP4, MP3, WAV, M4A, OGG, FLAC に対応。
    </div>
    """, unsafe_allow_html=True)

    # FFmpegの確認
    check_ffmpeg()

    # サイドバー設定
    with st.sidebar:
        st.header("⚙️ 設定")
        
        # モデル選択
        model_option = st.selectbox(
            "モデルサイズを選択",
            options=get_available_models(),
            index=1,  # baseをデフォルトに
            help="大きいモデルほど精度が上がりますが、処理時間も増加します。"
        )
        
        # 言語選択
        language_option = st.selectbox(
            "言語を選択",
            options=["", "ja", "en", "zh", "de", "fr", "es", "ko", "ru"],
            index=1,
            format_func=lambda x: {
                "": "自動検出",
                "en": "英語",
                "ja": "日本語",
                "zh": "中国語",
                "de": "ドイツ語",
                "fr": "フランス語",
                "es": "スペイン語",
                "ko": "韓国語",
                "ru": "ロシア語"
            }.get(x, x),
            help="音声の言語を指定します。自動検出も可能です。"
        )

        st.markdown("---")
        
        # デバイス情報表示
        device = "GPU (CUDA)" if torch.cuda.is_available() else "CPU"
        st.info(f"🖥️ 使用デバイス: {device}")
        if device == "CPU":
            st.warning("⚠️ GPUが検出されませんでした。処理が遅くなる可能性があります。")
            
        st.markdown("---")
        st.markdown("Built with OpenAI Whisper & Streamlit")

    # メインコンテンツ layout
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("ファイルアップロード")
        # ファイルアップロード (Added mp4 and mov)
        uploaded_file = st.file_uploader(
            "音声/動画ファイルをドラッグ＆ドロップ", 
            type=["mp3", "wav", "m4a", "ogg", "flac", "mp4", "mov", "mkv", "webm"],
            help="対応フォーマット: MP3, WAV, M4A, OGG, FLAC, MP4, MOV, MKV, WEBM"
        )

    if uploaded_file is not None:
        file_ext = uploaded_file.name.split('.')[-1].lower()
        
        with col2:
            st.subheader("プレビュー")
            # ファイル情報表示
            file_size_mb = uploaded_file.size / (1024 * 1024)
            st.info(f"ファイル名: {uploaded_file.name}\nサイズ: {file_size_mb:.2f} MB")
            
            # 再生機能 (Video for video files, Audio for audio files)
            if file_ext in ['mp4', 'mov', 'mkv', 'webm']:
                 st.video(uploaded_file)
            else:
                 st.audio(uploaded_file, format=f"audio/{file_ext}")

        st.markdown("---")

        # 文字起こし実行ボタン
        transcribe_button = st.button("🚀 文字起こし開始", type="primary")

        if transcribe_button:
            # 処理開始
            with st.spinner("⏳ 文字起こし処理中... モデルのロードと解析を行っています。"):
                # 一時ファイルとして保存
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    temp_filename = tmp_file.name

                try:
                    # モデルロード
                    start_time = time.time()
                    model = load_whisper_model(model_option)
                    model_load_time = time.time() - start_time
                    
                    # 文字起こし処理
                    transcribe_start = time.time()
                    
                    # 言語オプション設定
                    options = {}
                    if language_option:
                        options["language"] = language_option
                    
                    # 文字起こし実行
                    result = model.transcribe(temp_filename, **options)
                    
                    transcribe_time = time.time() - transcribe_start
                    total_time = time.time() - start_time

                    # 結果表示
                    st.success(f"✅ 処理完了！ (モデルロード: {model_load_time:.2f}秒, 文字起こし: {transcribe_time:.2f}秒, 合計: {total_time:.2f}秒)")
                    
                    # タブで表示切り替え
                    tab1, tab2, tab3 = st.tabs(["📄 テキスト全文", "⏱️ タイムスタンプ詳細", "📥 ダウンロード"])
                    
                    with tab1:
                        st.text_area("文字起こし結果", value=result["text"], height=300, key="transcript_text")
                        
                        # Copy button using Pyperclip (server-side/local)
                        if st.button("📋 クリップボードにコピー", key="copy_btn"):
                            try:
                                pyperclip.copy(result["text"])
                                st.success("✅ コピーしました！")
                            except Exception as e:
                                st.error(f"コピーに失敗しました: {e}")
                    
                    with tab2:
                        # テーブル表示用のデータ準備
                        table_data = []
                        timestamp_text = ""
                        for segment in result["segments"]:
                            start = segment["start"]
                            end = segment["end"]
                            text = segment["text"]
                            
                            # 時間をフォーマット (HH:MM:SS)
                            def format_timestamp(seconds):
                                m, s = divmod(seconds, 60)
                                h, m = divmod(m, 60)
                                return f"{int(h):02d}:{int(m):02d}:{s:06.3f}"
                            
                            start_fmt = format_timestamp(start)
                            end_fmt = format_timestamp(end)
                            
                            table_data.append({
                                "開始": start_fmt,
                                "終了": end_fmt,
                                "テキスト": text
                            })
                            timestamp_text += f"[{start_fmt} --> {end_fmt}] {text}\n"
                        
                        st.dataframe(table_data, use_container_width=True)

                    with tab3:
                        col_d1, col_d2 = st.columns(2)
                        with col_d1:
                            st.download_button(
                                label="📄 テキストのみダウンロード",
                                data=result["text"],
                                file_name=f"{os.path.splitext(uploaded_file.name)[0]}_transcript.txt",
                                mime="text/plain"
                            )
                        with col_d2:
                            st.download_button(
                                label="⏱️ タイムスタンプ付きダウンロード",
                                data=timestamp_text,
                                file_name=f"{os.path.splitext(uploaded_file.name)[0]}_transcript_timestamps.txt",
                                mime="text/plain"
                            )

                except Exception as e:
                    st.error(f"❌ エラーが発生しました: {str(e)}")
                
                finally:
                    # 一時ファイルの削除
                    if os.path.exists(temp_filename):
                        os.unlink(temp_filename)
                        
    else:
        # ファイルがアップロードされていない場合の案内
        st.info("👆 サイドバーでモデルを選択し、上のエリアにファイルをアップロードして開始してください。")
        
        with st.expander("ℹ️ 使い方・ヒント"):
            st.markdown("""
            1. **モデルサイズ**: `base` が推奨ですが、精度が足りない場合は `small` や `medium` を試してください。`large` は非常に時間がかかります。
            2. **言語**: 通常は「自動検出」でOKですが、短い音声や雑音が多い場合は明示的に指定すると精度が上がることがあります。
            3. **GPU**: CUDA対応のGPUがあると劇的に高速化します。
            """)

if __name__ == "__main__":
    main()
