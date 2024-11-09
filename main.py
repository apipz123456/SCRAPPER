import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from io import BytesIO
import json

# Fungsi untuk mengambil komentar dari YouTube menggunakan API
def video_comments(api_key, video_id):
    replies = []
    try:
        # Membuat koneksi ke YouTube API
        youtube = build('youtube', 'v3', developerKey=api_key)
        video_response = youtube.commentThreads().list(part='snippet,replies', videoId=video_id).execute()
        
        # Loop untuk mengambil semua komentar
        while video_response:
            for item in video_response['items']:
                published = item['snippet']['topLevelComment']['snippet']['publishedAt']
                user = item['snippet']['topLevelComment']['snippet']['authorDisplayName']
                comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
                likeCount = item['snippet']['topLevelComment']['snippet']['likeCount']
                replies.append([published, user, comment, likeCount])

                # Jika ada balasan komentar
                replycount = item['snippet']['totalReplyCount']
                if replycount > 0:
                    for reply in item['replies']['comments']:
                        published = reply['snippet']['publishedAt']
                        user = reply['snippet']['authorDisplayName']
                        repl = reply['snippet']['textDisplay']
                        likeCount = reply['snippet']['likeCount']
                        replies.append([published, user, repl, likeCount])

            # Memeriksa halaman berikutnya
            if 'nextPageToken' in video_response:
                video_response = youtube.commentThreads().list(
                    part='snippet,replies',
                    pageToken=video_response['nextPageToken'],
                    videoId=video_id
                ).execute()
            else:
                break
    except HttpError as e:
        # Penanganan error dari Google API
        error_message = json.loads(e.content).get('error', {}).get('message', 'Unknown error')
        st.error(f"Gagal mengambil komentar: {error_message}. Pastikan API Key dan Video ID benar.")
        return []
    except Exception as e:
        # Penanganan error lain
        st.error(f"Terjadi kesalahan: {str(e)}")
        return []
    
    return replies

# Streamlit App
def show():
    st.title("SCRAPING YOUTUBE UNTUK PKM GO SENTIMEN ANALISIS...")

    # Input API Key dan Video ID
    st.markdown("Belum memiliki API Key? [Klik DiSini](https://developers.google.com/youtube/v3/getting-started) untuk mendapatkannya.")
    api_key = st.text_input("Masukkan API Key YouTube:")
    video_id = st.text_input("Masukkan Video ID YouTube, contoh [v=_vJBuzzmS**]:")

    # Tombol untuk mulai scraping
    if st.button("Scrape Komentar"):
        if api_key and video_id:
            comments = video_comments(api_key, video_id)
            if comments:
                # Menyimpan hasil di session state agar tetap ada
                st.session_state['comments'] = pd.DataFrame(comments, columns=['publishedAt', 'authorDisplayName', 'textDisplay', 'likeCount'])
                st.write(st.session_state['comments'])
            else:
                st.warning("Tidak ada komentar ditemukan atau Video ID salah.")
        else:
            st.warning("Silakan masukkan API Key dan Video ID.")

    # Tampilkan opsi download jika komentar sudah di-scrape
    if 'comments' in st.session_state:
        df = st.session_state['comments']

        # Siapkan data untuk unduhan
        csv = df.to_csv(index=False).encode('utf-8')
        xlsx_output = BytesIO()
        with pd.ExcelWriter(xlsx_output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        xlsx_data = xlsx_output.getvalue()
        json_data = df.to_json(orient='records')

        # Pilihan format data
        format_option = st.selectbox("Pilih format untuk diunduh:", ["CSV", "XLSX", "JSON"])

        # Tombol untuk mengunduh data berdasarkan format pilihan
        if format_option == "CSV":
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name='youtube_comments.csv',
                mime='text/csv'
            )
        elif format_option == "XLSX":
            st.download_button(
                label="Download XLSX",
                data=xlsx_data,
                file_name='youtube_comments.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        elif format_option == "JSON":
            st.download_button(
                label="Download JSON",
                data=json_data,
                file_name='youtube_comments.json',
                mime='application/json'
            )

if __name__ == "__main__":
    show()
#bg
