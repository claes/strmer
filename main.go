package main

import (
	"bufio"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"net"
	"net/http"
	"os"
	"os/exec"
	"strings"
	"sync"
	"time"
)

type Subtitle struct {
	url          string
	lang         string
	subtitleType string
}

type Response struct {
	StreamURL string `json:"streamURL"`
}

func main() {

	// subs, _ := getAvailableSubtitles("https://www.youtube.com/watch?v=h6fcK_fRYaI")
	// for lang, urls := range subs {
	// 	fmt.Printf("%s: %v\n", lang, urls)
	// }
	port := flag.Int("port", 9090, "Port to run the server on")
	flag.Parse()
	err := startServer(*port)
	if err != nil {
		fmt.Printf("Failed to start server: %v\n", err)
	}
}

func startServer(port int) error {
	http.HandleFunc("/stream", streamHandler)
	fmt.Printf("Server started on :%d", port)
	err := http.ListenAndServe(fmt.Sprintf(":%d", port), nil)
	return err
}

func streamHandler(w http.ResponseWriter, r *http.Request) {
	// Get the URL from query parameters
	url := r.URL.Query().Get("url")
	if url == "" {
		http.Error(w, "Missing 'url' query parameter", http.StatusBadRequest)
		return
	}

	serveUrl, err := fetchAndServe(url, time.Second*10)
	if err != nil {
		http.Error(w, fmt.Sprintf("Could not prepare stream due to error: %v", err), 500)
		return
	}

	// Process the URL (for example, return the same URL but can be modified as needed)
	response := Response{StreamURL: serveUrl}

	// Encode response as JSON
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func args1(youtubeUrl string, subtitlesFile string, port int) ([]string, []string) {
	// working to file:
	// yt-dlp -f "(bv*[vcodec~='^((he|a)vc|h26[45])']+ba*[ext=m4a]) / (bv*+ba/b)" -o - 'https://www.youtube.com/watch?v=BZQ_ghBZrM0' | ffmpeg -i /tmp/subtitles.en.srt -i pipe: -movflags +faststart -c:v copy -c:a copy -c:s mov_text -f mp4       -listen 1 http://0.0.0.0:9898
	ytdlpArgs := []string{
		"-f", "(bv*[vcodec~='^((he|a)vc|h26[45])']+ba*[ext=m4a]) / (bv*+ba/b)",
		"-o", "-", youtubeUrl,
	}
	ffmpegArgs := []string{
		"-i", subtitlesFile,
		"-i", "pipe:",
		"-movflags", "+faststart",
		"-c:v", "copy",
		"-c:a", "copy",
		"-c:s", "mov_text",
		"-f", "mp4",
		"-listen", "1", fmt.Sprintf("http://0.0.0.0:%d", port),
	}
	return ytdlpArgs, ffmpegArgs
}

func args2(youtubeUrl string, subtitlesFile string, port int) ([]string, []string) {
	// streaming with subtitles!!
	// yt-dlp -f "(bv*[vcodec~='^((he|a)vc|h26[45])']+ba*[ext=m4a]) / (bv*+ba/b)" -o - 'https://www.youtube.com/watch?v=BZQ_ghBZrM0' | ffmpeg -i /tmp/subtitles.en.srt -i pipe: -movflags +faststart+frag_keyframe+empty_moov -bsf:a aac_adtstoasc -c:v copy -c:a copy -c:s mov_text -f mp4 -listen 1 http://0.0.0.0:8787
	ytdlpArgs := []string{
		"-f", "(bv*[vcodec~='^((he|a)vc|h26[45])']+ba*[ext=m4a]) / (bv*+ba/b)",
		"-o", "-", youtubeUrl,
	}

	ffmpegArgs := []string{
		"-i", subtitlesFile,
		"-i", "pipe:",
		"-movflags", "+faststart+frag_keyframe+empty_moov",
		"-bsf:a", "aac_adtstoasc",
		"-c:v", "copy",
		"-c:a", "copy",
		"-c:s", "mov_text",
		"-f", "mp4",
		"-listen", "1", fmt.Sprintf("http://0.0.0.0:%d", port),
	}
	return ytdlpArgs, ffmpegArgs
}

func args2_1(youtubeUrl string, subtitle Subtitle, port int) ([]string, []string) {
	// streaming with subtitles!!
	// yt-dlp -f "(bv*[vcodec~='^((he|a)vc|h26[45])']+ba*[ext=m4a]) / (bv*+ba/b)" -o - 'https://www.youtube.com/watch?v=BZQ_ghBZrM0' | ffmpeg -i /tmp/subtitles.en.srt -i pipe: -movflags +faststart+frag_keyframe+empty_moov -bsf:a aac_adtstoasc -c:v copy -c:a copy -c:s mov_text -f mp4 -listen 1 http://0.0.0.0:8787
	ytdlpArgs := []string{
		"-f", "(bv*[vcodec~='^((he|a)vc|h26[45])']+ba*[ext=m4a]) / (bv*+ba/b)",
		"-o", "-", youtubeUrl,
	}

	ffmpegArgs := []string{
		"-i", subtitle.url,
		"-i", "pipe:",
		"-movflags", "+faststart+frag_keyframe+empty_moov",
		"-bsf:a", "aac_adtstoasc",
		"-c:v", "copy",
		"-c:a", "copy",
		"-c:s", "mov_text",
		"-metadata:s:s:0", "language=" + subtitle.lang,
		"-metadata:s:s:0", "title=" + subtitle.lang,
		"-f", "mp4",
		"-listen", "1", fmt.Sprintf("http://0.0.0.0:%d", port),
	}
	return ytdlpArgs, ffmpegArgs
}

func args3(youtubeUrl string, subtitlesFile string, muxedFile string) ([]string, []string) {
	// streaming to file allowing file to be viewed while being written to
	// yt-dlp -f "(bv*[vcodec~='^((he|a)vc|h26[45])']+ba*[ext=m4a]) / (bv*+ba/b)" -o - 'https://www.youtube.com/watch?v=BZQ_ghBZrM0' | ffmpeg -i /tmp/subtitles.en.srt -i pipe: -movflags +faststart+frag_keyframe+empty_moov -bsf:a aac_adtstoasc -c:v copy -c:a copy -c:s mov_text -f mp4 /tmp/urk8.mp4
	ytdlpArgs := []string{
		"-f", `"(bv*[vcodec~='^((he|a)vc|h26[45])']+ba*[ext=m4a]) / (bv*+ba/b)"`,
		"-o", "-", youtubeUrl,
	}

	ffmpegArgs := []string{
		"-i", subtitlesFile,
		"-i", "pipe:",
		"-movflags", "+faststart+frag_keyframe+empty_moov",
		"-bsf:a", "aac_adtstoasc",
		"-c:v", "copy",
		"-c:a", "copy",
		"-c:s", "mov_text",
		"-f", "mp4",
		muxedFile,
	}
	return ytdlpArgs, ffmpegArgs
}

func args4(youtubeUrl string, subtitlesFile string, port int) ([]string, []string) {
	// streaming and burning subtitles work
	// yt-dlp -f "(bv*[vcodec~='^((he|a)vc|h26[45])']+ba*[ext=m4a]) / (bv*+ba/b)" -o - 'https://www.youtube.com/watch?v=BZQ_ghBZrM0' | \
	// ffmpeg -i pipe: -vf subtitles=/tmp/subtitles.en.srt -c:v libx264 -preset ultrafast -c:a copy -f mpegts \
	// -listen 1 http://0.0.0.0:9898
	ytdlpArgs := []string{
		"-f", `"(bv*[vcodec~='^((he|a)vc|h26[45])']+ba*[ext=m4a]) / (bv*+ba/b)"`,
		"-o", "-", youtubeUrl,
	}

	ffmpegArgs := []string{
		"-i", "pipe:",
		"-vf", fmt.Sprintf("subtitles=%s", subtitlesFile),
		"-c:v", "copy",
		"-c:a", "libx264", "-preset", "ultrafast",
		"-c:s", "mov_text",
		"-f", "mpegts",
		"-listen", "1", fmt.Sprintf("http://0.0.0.0:%d", port),
	}
	return ytdlpArgs, ffmpegArgs
}

func getAvailableSubtitles(youtubeUrl string) (map[string][]Subtitle, error) {
	cmd := exec.Command("yt-dlp", "--dump-json", youtubeUrl)
	output, err := cmd.Output()
	if err != nil {
		return nil, fmt.Errorf("error running yt-dlp: %v", err)
	}

	var data map[string]interface{}
	if err := json.Unmarshal(output, &data); err != nil {
		return nil, fmt.Errorf("error parsing JSON output: %v", err)
	}

	// Extract available subtitles
	subtitles := make(map[string][]Subtitle)
	if subs, ok := data["subtitles"].(map[string]interface{}); ok {
		for lang, entries := range subs {
			if entryList, ok := entries.([]interface{}); ok {
				for _, entry := range entryList {
					if entryMap, ok := entry.(map[string]interface{}); ok {
						if url, ok := entryMap["url"].(string); ok {
							subtitle := Subtitle{url: url, subtitleType: entryMap["ext"].(string), lang: entryMap["name"].(string)}
							//urltype := []string{entryMap["ext"].(string), entryMap["name"].(string), url}
							subtitles[lang] = append(subtitles[lang], subtitle)
						}
					}
				}
			}
		}
	}

	return subtitles, nil
}

func downloadSubtiles(youtubeUrl string) (string, error) {

	subtitles, err := getAvailableSubtitles(youtubeUrl)
	if err != nil {
		return "", err
	}

	langs := []string{"sv-SE", "sv", "en", "en-US", "en-GB", "en-orig"}

	for _, lang := range langs {
		if _, exists := subtitles[lang]; exists {
			// Temporary subtitle file path
			subtitleFile := "/tmp/subtitles"
			downloadedSubtitleFile := subtitleFile + "." + lang + ".srt"

			// Separate arguments for subtitle download
			ytdlpSubtitleArgs := []string{
				"--skip-download", "--write-sub", "--sub-lang", lang, "--convert-subs", "srt",
				"-o", downloadedSubtitleFile, youtubeUrl,
			}

			// Download subtitles using yt-dlp
			err := exec.Command("yt-dlp", ytdlpSubtitleArgs...).Run()
			if err != nil {
				return "", fmt.Errorf("Error downloading subtitles with yt-dlp: %v", err)
			}

			// Check if the subtitle file exists
			if _, err := os.Stat(downloadedSubtitleFile); os.IsNotExist(err) {
				return "", fmt.Errorf("Subtitle file not found: %s", downloadedSubtitleFile)
			}
			return downloadedSubtitleFile, nil
		}
	}
	return "", errors.New("Subtitle not found")
}

func getSubtitle(youtubeUrl string) (Subtitle, error) {

	subtitles, err := getAvailableSubtitles(youtubeUrl)
	if err != nil {
		return Subtitle{}, err
	}

	langs := []string{"en", "en-US", "en-GB", "en-orig", "sv-SE", "sv"}

	for _, lang := range langs {
		if subtitle, exists := subtitles[lang]; exists {
			for _, s := range subtitle {
				if s.subtitleType == "vtt" {
					return s, nil
				}
			}
		}
	}
	return Subtitle{}, errors.New("Subtitle not found")
}

func fetchAndServe(youtubeUrl string, timeout time.Duration) (string, error) {
	streamPort, err := findAvailablePort()
	if err != nil {
		return "", fmt.Errorf("Could not find available port", err)
	}

	subtitle, _ := getSubtitle(youtubeUrl)
	if err != nil {
		return "", fmt.Errorf("Could not download subtitles", err)
	}

	ytdlpArgs, ffmpegArgs := args2_1(youtubeUrl, subtitle, streamPort)
	ytdlpCmd := exec.Command("yt-dlp", ytdlpArgs...)
	ffmpegCmd := exec.Command("ffmpeg", ffmpegArgs...)

	ytdlpStdOut, err := ytdlpCmd.StdoutPipe()
	if err != nil {
		return "", fmt.Errorf("Error creating stdout pipe for yt-dlp", err)
	}

	ytdlpStdErr, err := ytdlpCmd.StderrPipe()
	if err != nil {
		return "", fmt.Errorf("Error creating stderr pipe for yt-dlp", err)
	}

	ffmpegCmd.Stdin = ytdlpStdOut

	ffmpegStdOut, err := ffmpegCmd.StdoutPipe()
	if err != nil {
		return "", fmt.Errorf("Error creating stdout pipe for ffmpeg", err)
	}

	ffmpegStdErr, err := ffmpegCmd.StderrPipe()
	if err != nil {
		return "", fmt.Errorf("Error creating stderr pipe for ffmpeg", err)
	}

	var wg sync.WaitGroup
	wg.Add(2)

	foundSignal := make(chan string, 1)

	scanOutput := func(scanner *bufio.Scanner, searchString string, source string) {
		defer wg.Done()
		for scanner.Scan() {
			line := scanner.Text()
			fmt.Printf("[%s] %s\n", source, line)
			if strings.Contains(line, searchString) && "" != searchString {
				foundSignal <- fmt.Sprintf("Special string found in %s output: %s", source, line)
			}
		}
	}

	go func() {
		scanner := bufio.NewScanner(ytdlpStdErr)
		scanOutput(scanner, "Press [q] to stop", "ytdlp-stderr")
	}()

	if err := ytdlpCmd.Start(); err != nil {
		return "", fmt.Errorf("Error starting yt-dlp", err)
	}

	go func() {
		scanner := bufio.NewScanner(ffmpegStdOut)
		scanOutput(scanner, "", "ffmpeg-stdout")
	}()
	go func() {
		scanner := bufio.NewScanner(ffmpegStdErr)
		scanOutput(scanner, "", "ffmpeg-stderr")
	}()

	if err := ffmpegCmd.Start(); err != nil {
		return "", fmt.Errorf("Error starting ffmpeg", err)
	}

	select {
	case msg := <-foundSignal:
		fmt.Println(msg)
		return fmt.Sprintf("http://localhost:%d", streamPort), nil
	case <-time.After(timeout):
		fmt.Println("Special string not found in any output, timing out")
		return "", fmt.Errorf("Streaming failed")
	}
}

func findAvailablePort() (int, error) {
	// // Create a listener on a random port (port 0 lets the OS pick a free port)
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		return 0, err
	}
	defer listener.Close()

	addr := listener.Addr().(*net.TCPAddr)
	return addr.Port, nil
}
