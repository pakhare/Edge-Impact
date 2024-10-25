const videos = [
    { element: document.getElementById('video1'), src: 'https://videos.pexels.com/video-files/13221290/13221290-uhd_2560_1440_30fps.mp4' },
    { element: document.getElementById('video2'), src: 'https://videos.pexels.com/video-files/28552794/12418740_2560_1440_60fps.mp4' },
];


let currentVideo = 0;

// Function to play the next video
function playNextVideo() {
    if (currentVideo < videos.length) {
        // Hide the current video
        if (currentVideo > 0) {
            videos[currentVideo - 1].element.style.display = 'none';
        }

        // Load and play the next video
        const videoData = videos[currentVideo];
        videoData.element.src = videoData.src; // Set the source dynamically
        videoData.element.style.display = 'block';
        videoData.element.play();

        // Add event listener to play the next video when the current one ends
        videoData.element.onended = () => {
            currentVideo = (currentVideo + 1) % videos.length; 
            playNextVideo();
        };
    }
}

// Start playing the first video
playNextVideo();
