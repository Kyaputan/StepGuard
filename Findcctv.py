import cv2
import time
import os
import socket
from colorama import init, Fore, Style

# Initialize colorama for cross-platform colored terminal output
init(autoreset=True)

# Configuration - ปรับค่าเหล่านี้ได้ง่ายๆ
CONFIG = {
    'user': 'Rachata', #TODO: username
    'password': '12345678', #TODO: password
    'ip': '192.168.1.102', #TODO: ip address
    'ports_to_test': [554, 556, 1935, 80, 8080], 
    'open_timeout': 1500,
    'read_timeout': 800,
    'buffer_size': 1,
    'test_frames': 3,
    'vlc_test_frames': 2,
    'rtsp_urls': [
        '/stream1',
        ':554/stream1',
        '/live/stream1',
        '/cam/realmonitor?channel=1&subtype=0',
        '/Streaming/Channels/101',
        ':556/Streaming/Channels/1',
        ':556/',
    ],
    'vlc_urls': [
        ':554/stream1',
        ':554/stream2',
        ':556/stream1',
        ':556/stream2',
        '/live/stream1',
    ],
    'additional_urls': [
        # Common Hikvision patterns
        ':554/Streaming/Channels/1',
        ':554/Streaming/Channels/101/',
        ':554/Streaming/Channels/1/',
        # Common Dahua patterns
        ':554/cam/realmonitor?channel=1&subtype=1',
        '/live1.sdp',
        '/live2.sdp',
        # Generic patterns
        ':554/live',
        ':554/',
        '/1',
        '/channel1',
        '/media/video1',

        ':556/Streaming/Channels/1',
        ':556/Streaming/Channels/101/',
        ':556/Streaming/Channels/1/',
        ':556/',

    ]
}

def test_rtsp_urls(urls, User, Password, ip, backend_name='FFMPEG', test_frames=10):
    """Test RTSP URLs with given parameters"""
    successful_connections = []
    total_urls = len(urls)

    for i, url_suffix in enumerate(urls, 1):
        url = f"rtsp://{User}:{Password}@{ip}{url_suffix}"
        print(f"\n{Fore.CYAN}[{i}/{total_urls}]{Style.RESET_ALL} Testing: {Fore.YELLOW}{url}{Style.RESET_ALL}")

        try:
            backend = cv2.CAP_FFMPEG if backend_name == 'FFMPEG' else cv2.CAP_ANY
            cap = cv2.VideoCapture(url, backend)

            # Set properties from config
            cap.set(cv2.CAP_PROP_BUFFERSIZE, CONFIG['buffer_size'])
            cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, CONFIG['open_timeout'])
            cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, CONFIG['read_timeout'])

            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                    fps = cap.get(cv2.CAP_PROP_FPS)

                    print(f"   {Fore.GREEN}✓ SUCCESS!{Style.RESET_ALL} Resolution: {Fore.BLUE}{int(width)}x{int(height)}{Style.RESET_ALL}, FPS: {Fore.BLUE}{fps}{Style.RESET_ALL}")

                    # Test multiple frames
                    success_count = 0
                    print(f"   Testing {test_frames} frames...", end=" ")
                    for j in range(test_frames):
                        ret, frame = cap.read()
                        if ret:
                            success_count += 1
                        time.sleep(0.1)
                    print(f"{Fore.GREEN}{success_count}/{test_frames} successful{Style.RESET_ALL}")

                    successful_connections.append({
                        'url': url,
                        'backend': backend_name,
                        'resolution': f"{int(width)}x{int(height)}",
                        'fps': fps,
                        'frame_success_rate': f"{success_count}/{test_frames}"
                    })
                else:
                    print(f"   {Fore.RED}✗ Connected but no frames{Style.RESET_ALL}")
            else:
                print(f"   {Fore.RED}✗ Failed to connect{Style.RESET_ALL}")

            cap.release()

        except Exception as e:
            print(f"   {Fore.RED}✗ Error: {e}{Style.RESET_ALL}")

    return successful_connections

def test_rtsp_connection(User, Password, ip):
    """Test RTSP connection with various methods"""
    print(f"\n{Fore.MAGENTA}{'='*70}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}🔍 Testing RTSP connections...{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}{'='*70}{Style.RESET_ALL}")
    return test_rtsp_urls(CONFIG['rtsp_urls'], User, Password, ip, 'FFMPEG', CONFIG['test_frames'])

def test_with_vlc_method(User, Password, ip):
    """Test using VLC-like parameters"""
    print(f"\n{Fore.MAGENTA}{'='*70}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}🎬 Trying VLC-compatible method...{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}{'='*70}{Style.RESET_ALL}")
    return test_rtsp_urls(CONFIG['vlc_urls'], User, Password, ip, 'VLC-method', CONFIG['vlc_test_frames'])

def test_additional_urls(User, Password, ip):
    """Test additional common RTSP URL patterns"""
    print(f"\n{Fore.MAGENTA}{'='*70}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}🔧 Testing ADDITIONAL URL patterns...{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}{'='*70}{Style.RESET_ALL}")
    return test_rtsp_urls(CONFIG['additional_urls'], User, Password, ip, 'FFMPEG', 1)

def network_test(ip):
    """Test network connectivity"""
    print(f"\n{Fore.MAGENTA}{'='*70}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}🌐 Network Connectivity Test for {Fore.YELLOW}{ip}{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}{'='*70}{Style.RESET_ALL}")

    accessible_ports = 0
    total_ports = len(CONFIG['ports_to_test'])

    for i, port in enumerate(CONFIG['ports_to_test'], 1):
        print(f"{Fore.CYAN}[{i}/{total_ports}]{Style.RESET_ALL} Testing port {Fore.BLUE}{port}{Style.RESET_ALL}...", end=" ")
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((ip, port))
            sock.close()

            if result == 0:
                print(f"{Fore.GREEN}✓ Accessible{Style.RESET_ALL}")
                accessible_ports += 1
            else:
                print(f"{Fore.RED}✗ Not accessible{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}✗ Error: {e}{Style.RESET_ALL}")

    print(f"\n{Fore.GREEN}Accessible ports: {accessible_ports}/{total_ports}{Style.RESET_ALL}")

if __name__ == "__main__":
    os.system('cls' if os.name == 'nt' else 'clear')

    # ใช้ค่าจาก CONFIG
    User = CONFIG['user']
    Password = CONFIG['password']
    ip = CONFIG['ip']

    network_test(ip)
    successful_main = test_rtsp_connection(User, Password, ip)
    successful_vlc = test_with_vlc_method(User, Password, ip)
    successful_additional = test_additional_urls(User, Password, ip)
    all_successful = successful_main + successful_vlc + successful_additional
    
    # Print summary with colors and better formatting
    print(f"\n{Fore.MAGENTA}{'='*80}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'🎯 COMPLETE SUMMARY OF ALL TESTS':^80}{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}{'='*80}{Style.RESET_ALL}")

    if all_successful:
        print(f"\n{Fore.GREEN}🎉 FOUND {len(all_successful)} WORKING CONNECTIONS!{Style.RESET_ALL}")

        # Print table header
        print(f"\n{Fore.YELLOW}{'─'*80}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}| {'#':<2} | {'URL':<40} | {'Backend':<10} | {'Resolution':<10} | {'FPS':<4} | {'Frames':<6} |{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}{'─'*80}{Style.RESET_ALL}")

        # Print each successful connection in table format
        for i, conn in enumerate(all_successful, 1):
            url_short = conn['url'][:38] + "..." if len(conn['url']) > 38 else conn['url']
            print(f"{Fore.WHITE}| {i:<2} | {url_short:<40} | {conn['backend']:<10} | {conn['resolution']:<10} | {conn['fps']:<4} | {conn['frame_success_rate']:<6} |{Style.RESET_ALL}")

        print(f"{Fore.YELLOW}{'─'*80}{Style.RESET_ALL}")

        # Find best connection
        best_connection = max(all_successful, key=lambda x: (float(x['fps']) if x['fps'] > 0 else 0, int(x['frame_success_rate'].split('/')[0])))

        print(f"\n{Fore.GREEN}🏆 RECOMMENDED CONNECTION (Best Performance):{Style.RESET_ALL}")
        print(f"   {Fore.BLUE}URL:{Style.RESET_ALL} {best_connection['url']}")
        print(f"   {Fore.BLUE}Backend:{Style.RESET_ALL} {best_connection['backend']}")
        print(f"   {Fore.BLUE}Resolution:{Style.RESET_ALL} {best_connection['resolution']}")
        print(f"   {Fore.BLUE}FPS:{Style.RESET_ALL} {best_connection['fps']}")

        print(f"\n{Fore.CYAN}📝 Example code:{Style.RESET_ALL}")
        backend_code = "cv2.CAP_FFMPEG" if best_connection['backend'] in ["FFMPEG", "VLC-method"] else f"cv2.CAP_{best_connection['backend']}"
        print(f"{Fore.GREEN}cap = cv2.VideoCapture('{best_connection['url']}', {backend_code}){Style.RESET_ALL}")
        print(f"{Fore.GREEN}cap.set(cv2.CAP_PROP_BUFFERSIZE, 1){Style.RESET_ALL}")

    else:
        print(f"\n{Fore.RED}❌ NO SUCCESSFUL RTSP CONNECTIONS FOUND{Style.RESET_ALL}")
        print(f"\n{Fore.YELLOW}🔧 Troubleshooting suggestions:{Style.RESET_ALL}")
        print(f"   1. {Fore.WHITE}Check if the camera is accessible from your network{Style.RESET_ALL}")
        print(f"   2. {Fore.WHITE}Verify username/password are correct{Style.RESET_ALL}")
        print(f"   3. {Fore.WHITE}Try different stream paths (/stream2, /live, etc.){Style.RESET_ALL}")
        print(f"   4. {Fore.WHITE}Check if OpenCV was compiled with FFMPEG support{Style.RESET_ALL}")
        print(f"      {Fore.GRAY}- Run: python -c \"import cv2; print(cv2.getBuildInformation())\"{Style.RESET_ALL}")
        print(f"   5. {Fore.WHITE}Try installing additional codecs{Style.RESET_ALL}")
        print(f"   6. {Fore.WHITE}Check camera documentation for correct RTSP URLs{Style.RESET_ALL}")
        print(f"   7. {Fore.WHITE}Try accessing the camera web interface first{Style.RESET_ALL}")
        print(f"   8. {Fore.WHITE}Verify the camera supports RTSP protocol{Style.RESET_ALL}")

    # Print test summary with colors
    print(f"\n{Fore.CYAN}📊 Test Summary:{Style.RESET_ALL}")
    print(f"   {Fore.BLUE}Main URL patterns:{Style.RESET_ALL} {Fore.GREEN}{len(successful_main)} successful{Style.RESET_ALL}")
    print(f"   {Fore.BLUE}VLC method:{Style.RESET_ALL} {Fore.GREEN}{len(successful_vlc)} successful{Style.RESET_ALL}")
    print(f"   {Fore.BLUE}Additional URL patterns:{Style.RESET_ALL} {Fore.GREEN}{len(successful_additional)} successful{Style.RESET_ALL}")
    print(f"   {Fore.BLUE}Total successful connections:{Style.RESET_ALL} {Fore.GREEN}{len(all_successful)}{Style.RESET_ALL}")