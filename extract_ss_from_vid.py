import os
import argparse
import multiprocessing
import cv2
import numpy as np
from tqdm import tqdm
import youtube_dl


YOUTUBE_DL_OPTIONS = {
    "format": "bestvideo[ext=mp4][height<=1080]/best[ext=mp4][height<=1080]",
    "outtmpl": "%(uploader)s-%(id)s.%(ext)s",
}
THRESHOLD = 0.2
SKIP = 10
DROP_TEXT_TEMPLATE = "template/drop_text.png"


def recognize_drop_text(frame, template, name):
    res = cv2.matchTemplate(frame, template, cv2.TM_SQDIFF_NORMED)
    loc = np.where(res < THRESHOLD)
    # loc is empty if the frame doesn't match
    # return loc[0].size > 0
    if loc[0].size > 0:
        cv2.imwrite(name, frame)


def extract_drop_screen(file, output_folder, processes):
    cap = cv2.VideoCapture(file)
    template = cv2.imread(DROP_TEXT_TEMPLATE)
    total_frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    pool = multiprocessing.Pool(processes=processes)
    with tqdm(total=total_frame_count) as pbar:
        while cap.isOpened():
            ret, frame = cap.read()
            frame_id = cap.get(cv2.CAP_PROP_POS_FRAMES)
            if ret:
                if frame_id % SKIP == 0:
                    pool.apply_async(
                        recognize_drop_text,
                        (
                            frame.copy(),
                            template,
                            os.path.join(output_folder, f"{file}_{frame_id}.png"),
                        ),
                    )
                pbar.update(1)
            else:
                break
    cap.release()


def run(link, quest, processes):
    quest_folder = os.path.join("input", str(quest))
    if not os.path.isdir(quest_folder):
        os.mkdir(quest_folder)
    if os.path.exists(link):
        file_name = link
    else:
        try:
            ydl = youtube_dl.YoutubeDL(YOUTUBE_DL_OPTIONS)
            ydl.add_default_info_extractors()
            info = ydl.extract_info(link)
            file_name = f"{info['uploader']}-{info['id']}.mp4"
        except (youtube_dl.utils.UnsupportedError, youtube_dl.utils.DownloadError):
            pass
    extract_drop_screen(file_name, quest_folder, processes)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Get drop screenshots from Youtube link"
    )
    parser.add_argument("-i", "--input", help="File or Youtube link to download")
    parser.add_argument(
        "-q",
        "--quest",
        help="Output quest folder in input folder",
        default="video_screenshot",
    )
    parser.add_argument(
        "-n",
        "--num-processes",
        help="Number of processes to run",
        default=cv2.getNumberOfCPUs(),
    )
    args = parser.parse_args()

    run(args.input, args.quest, args.processes)