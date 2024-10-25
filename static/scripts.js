const videos = [
    { element: document.getElementById('video1'), src: '/static/video1.mp4' },
    { element: document.getElementById('video2'), src: '/static/video2.mp4' },
    { element: document.getElementById('video3'), src: '/static/video3.mp4' }
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
