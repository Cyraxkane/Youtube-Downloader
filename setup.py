# setup.py
from setuptools import setup, find_packages

setup(
    name='album_downloader',
    version='1.0.0',
    author='CyraxKane',
    author_email='zayyarhein645@example.com',  # Optional
    description='Download single videos or playlists as MP3 or MP4 using yt-dlp',
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/Cyraxkane/Youtube-Downloader.git',  # Update if published
    packages=find_packages(),
    py_modules=['downloader'],
    install_requires=[
        'yt-dlp>=2024.3.10'
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    entry_points={
        'console_scripts': [
            'album-downloader=downloader:main',
        ],
    },
    python_requires='>=3.7',
)
