import os
from flask import Flask, request, send_file, render_template_string, jsonify, Response
import yt_dlp
import ffmpeg

app = Flask(__name__)
# def download_video_with_quality(url, output_dir, quality):
#     ydl_opts = {
#         'format': quality,
#         'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
#     }
#
#     with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#         info = ydl.extract_info(url, download=True)
#         video_title = info.get('title', 'unknown_title')
#         video_file = info.get('requested_downloads', [{}])[0].get('filepath')
#
#         # Ensure both audio and video exist before merging
#         if len(info.get('requested_downloads', [])) > 1:
#             audio_file = info['requested_downloads'][1]['filepath']
#             merged_output = os.path.join(output_dir, f"{video_title}_merged.mp4")
#             ffmpeg.input(video_file).output(audio_file).output(merged_output).run(overwrite_output=True)
#             return {
#                 'video_title': video_title,
#                 'video_file_path': merged_output
#             }
#         return {
#             'video_title': video_title,
#             'video_file_path': video_file
#         }


def download_video_with_quality(url, output_dir, quality):
    ydl_opts = {
        'format': quality,
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        video_title = info.get('title', 'unknown_title')
        video_file = info.get('requested_downloads', [{}])[0].get('filepath')

        # Ensure both audio and video exist before merging
        if len(info.get('requested_downloads', [])) > 1:
            audio_file = info['requested_downloads'][1]['filepath']
            merged_output = os.path.join(output_dir, f"{video_title}_merged.mp4")
            ffmpeg.input(video_file).output(audio_file).output(merged_output).run(overwrite_output=True)
            return {
                'video_title': video_title,
                'video_file_path': merged_output
            }
        return {
            'video_title': video_title,
            'video_file_path': video_file
        }


# Fetch available resolutions
def get_available_resolutions(url):
    ydl_opts = {'format': 'best'}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        formats = info.get('formats', [])
        resolutions = []
        for fmt in formats:
            if fmt.get('vcodec') != 'none':
                height = fmt.get('height')
                if height and height >= 144:
                    resolutions.append({'quality': fmt['format_id'], 'resolution': f"{height}p"})
        return sorted(resolutions, key=lambda x: int(x['resolution'].replace('p', '')))


# Serve the HTML page
@app.route('/ytd')
def home():
    html_content = """
    <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Youtube Video Downloader</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
            margin: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            color: #333;
        }
        .container {
            background: #ffffff;
            border: 1px solid #ddd;
            border-radius: 10px;
            padding: 25px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
            text-align: center;
            width: 90%;
            max-width: 500px;
        }
        h2 {
            margin-bottom: 20px;
            font-size: 22px;
            font-weight: normal;
        }
        input, select, button {
            width: 100%;
            margin: 10px 0;
            padding: 12px;
            border: 1px solid #ccc;
            border-radius: 8px;
            font-size: 16px;
            box-sizing: border-box;
        }
        input {
            background-color: #f9f9f9;
        }
        input::placeholder {
            color: #aaa;
        }
        select {
            background-color: #f9f9f9;
        }
        button {
            background-color: #888888;
            color: white;
            border: none;
            cursor: pointer;
            transition: background 0.3s ease;
            border-radius: 50px;
        }
        button:hover {
            background-color: #555555;
        }
        #loading {
            margin-top: 20px;
            display: none;
        }
        .spinner {
            width: 35px;
            height: 35px;
            border: 4px solid rgba(150, 150, 150, 0.3);
            border-radius: 50%;
            border-top: 4px solid #555;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin {
            from {
                transform: rotate(0deg);
            }
            to {
                transform: rotate(360deg);
            }
        }
        .video-title {
            margin-top: 10px;
            font-size: 16px;
            font-weight: normal;
            color: #555;
        }
        footer {
            margin-top: 20px;
            font-size: 12px;
            color: #777;
        }
    </style>
</head>
<body>
    <div class="container">
        <h2>Youtube Video Downloader</h2>
        <input type="text" id="urlInput" placeholder="Enter the video URL here" />
        <button onclick="fetchResolutions()">Fetch Resolutions</button>
        <div id="loading">
            <div class="spinner"></div>
            <p>Fetching video info...</p>
        </div>
        <div id="videoDetails" style="display: none;">
            <h3 class="video-title" id="videoTitle"></h3>
            <select id="qualitySelect"></select>
            <button onclick="downloadFile()">Download</button>
        </div>
    </div>
    <footer>
        Developed by <strong>Your Name</strong>.
    </footer>

    <script>
        function fetchResolutions() {
            const urlInput = document.getElementById('urlInput').value.trim();
            if (!urlInput) {
                alert('Please enter a valid URL!');
                return;
            }

            const loading = document.getElementById('loading');
            const videoDetails = document.getElementById('videoDetails');
            const videoTitle = document.getElementById('videoTitle');
            const qualitySelect = document.getElementById('qualitySelect');

            loading.style.display = 'block';
            videoDetails.style.display = 'none';
            videoTitle.textContent = '';
            qualitySelect.innerHTML = '';

            fetch(`/get_resolutions?url=${encodeURIComponent(urlInput)}`)
                .then(response => response.json())
                .then(data => {
                    loading.style.display = 'none';

                    if (data.error) {
                        alert(data.error);
                        return;
                    }

                    // Populate video title
                    videoTitle.textContent = `${data.title || 'Unknown'}`;

                    // Populate resolutions dropdown
                    data.resolutions.forEach(res => {
                        const option = document.createElement('option');
                        option.value = res.quality;
                        option.textContent = res.resolution;
                        qualitySelect.appendChild(option);
                    });

                    // Show video details
                    videoDetails.style.display = 'block';
                })
                .catch(err => {
                    loading.style.display = 'none';
                    alert('Error fetching resolutions. Make sure the link is valid.');
                });
        }

      
    function downloadFile() {
        const urlInput = document.getElementById('urlInput').value.trim();
        const quality = document.getElementById('qualitySelect').value;

        if (!urlInput || !quality) {
            alert('Please select a quality!');
            return;
        }

        const loading = document.getElementById('loading');
        loading.style.display = 'block';

        fetch(`/download?url=${encodeURIComponent(urlInput)}&quality=${encodeURIComponent(quality)}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Error downloading video');
                }
                return response.blob();
            })
            .then(blob => {
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `video_${quality}.mp4`;
                a.click();
                window.URL.revokeObjectURL(url);

                // Reset the page after the download is initiated
                alert('Download started successfully. The page will reset now.');
                window.location.reload();
            })
            .catch(err => {
                loading.style.display = 'none';
                alert(err.message);
            });
    }
</script>

    </script>
</body>
</html>

    """
    return render_template_string(html_content)

@app.route('/download', methods=['GET'])
def download_video_endpoint():
    video_url = request.args.get('url')
    quality = request.args.get('quality')
    if not video_url or not quality:
        return "Missing parameters", 400
    try:
        output_dir = os.path.abspath('downloads')
        os.makedirs(output_dir, exist_ok=True)
        result = download_video_with_quality(video_url, output_dir, quality)
        video_file_path = result['video_file_path']

        if not os.path.isfile(video_file_path):
            return jsonify({"error": "File not found"}), 404

        return send_file(video_file_path, as_attachment=True)
    except Exception as e:
        return f"Error downloading video: {str(e)}", 500


# @app.route('/download', methods=['GET'])
# def download_video_endpoint():
#     video_url = request.args.get('url')
#     quality = request.args.get('quality')
#     if not video_url or not quality:
#         return "Missing parameters", 400
#
#     try:
#         output_dir = os.path.abspath('downloads')
#         os.makedirs(output_dir, exist_ok=True)
#
#         # Start video download in the background and stream it
#         def generate():
#             result = download_video_with_quality(video_url, output_dir, quality)
#             video_file_path = result['video_file_path']
#             with open(video_file_path, 'rb') as video_file:
#                 while chunk := video_file.read(1024 * 1024):  # Read in 1MB chunks
#                     yield chunk
#
#         return Response(generate(), content_type='video/mp4')
#     except Exception as e:
#         return f"Error: {e}", 500


@app.route('/get_resolutions', methods=['GET'])
def get_resolutions():
    video_url = request.args.get('url')
    if not video_url:
        return jsonify({'error': "Missing 'url' parameter"}), 400
    try:
        with yt_dlp.YoutubeDL({'format': 'best'}) as ydl:
            info = ydl.extract_info(video_url, download=False)
            video_title = info.get('title', 'Unknown Title')
            formats = info.get('formats', [])
            resolutions = {}

            # Iterate through formats and extract unique resolutions
            for fmt in formats:
                if fmt.get('vcodec') != 'none':  # Ensure it's a video format
                    height = fmt.get('height')
                    if height and height >= 144:  # Filter resolutions of 144p and above
                        format_id = fmt.get('format_id')
                        resolution = f"{height}p"
                        # Store the resolution with its corresponding quality key
                        if resolution not in resolutions:
                            resolutions[resolution] = {'quality': format_id, 'resolution': resolution}

            # Convert the dictionary values to a list and sort by resolution height
            sorted_resolutions = sorted(resolutions.values(), key=lambda x: int(x['resolution'].replace('p', '')))

            return jsonify({'title': video_title, 'resolutions': sorted_resolutions})
    except Exception as e:
        return jsonify({'error': str(e)}), 500



if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=443)
