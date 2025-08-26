import cv2
import time
import os
import socket

def test_rtsp_connection(User, Password, ip):
    """Test RTSP connection with various methods - Test ALL combinations"""
    
    base_url = f"rtsp://{User}:{Password}@{ip}"
    rtsp_urls = [
        f"{base_url}/stream1",
        f"{base_url}:554/stream1", 
        f"{base_url}/live/stream1",
        f"{base_url}/h264",
        f"{base_url}/cam/realmonitor?channel=1&subtype=0",
        f"{base_url}/onvif1",
        f"{base_url}/Streaming/Channels/101",
        f"{base_url}/videoMain"
    ]
    
    print("Testing ALL RTSP connections...")
    print("=" * 70)
    
    successful_connections = []
    
    for i, url in enumerate(rtsp_urls, 1):
        print(f"\n{i}. Testing: {url}")
        print("-" * 50)

        backends = [
            (cv2.CAP_FFMPEG, "FFMPEG"),
            (cv2.CAP_GSTREAMER, "GStreamer"), 
            (cv2.CAP_ANY, "Any")
        ]
        
        for backend, backend_name in backends:
            try:
                print(f"   Trying {backend_name} backend...")
                cap = cv2.VideoCapture(url, backend)
                
                # Set properties
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)
                cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 3000)
                
                if cap.isOpened():
                    print(f"   ✓ Connected with {backend_name}!")
                    
                    # Try to read a frame
                    ret, frame = cap.read()
                    if ret:
                        print(f"   ✓ Successfully read frame: {frame.shape}")
                        
                        # Show properties
                        width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                        height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                        fps = cap.get(cv2.CAP_PROP_FPS)
                        
                        print(f"   Resolution: {int(width)}x{int(height)}")
                        print(f"   FPS: {fps}")
                        
                        # Test reading multiple frames
                        print("   Testing frame reading...")
                        success_count = 0
                        for j in range(10):  # เปลี่ยนกลับเป็น 10 ตามโค้ดเดิม
                            ret, frame = cap.read()
                            if ret:
                                success_count += 1
                            time.sleep(0.1)
                        
                        print(f"   Successfully read {success_count}/10 frames")
                        
                        # เก็บข้อมูลการเชื่อมต่อที่สำเร็จ
                        successful_connections.append({
                            'url': url,
                            'backend': backend_name,
                            'resolution': f"{int(width)}x{int(height)}",
                            'fps': fps,
                            'frame_success_rate': f"{success_count}/10"
                        })
                        
                    else:
                        print(f"   ✗ Connected but couldn't read frames")
                else:
                    print(f"   ✗ Failed to connect with {backend_name}")
                
                cap.release()
                
            except Exception as e:
                print(f"   ✗ Error with {backend_name}: {e}")
    
    return successful_connections

def test_with_vlc_method(User, Password, ip):
    """Test using VLC-like parameters"""
    print("\n" + "=" * 50)
    print("Trying VLC-compatible method...")
    print("=" * 50)
    
    vlc_urls = [
        f"rtsp://{User}:{Password}@{ip}:554/stream1",
        f"rtsp://{User}:{Password}@{ip}:554/stream2",
        f"rtsp://{User}:{Password}@{ip}/live/stream1",
        f"rtsp://{User}:{Password}@{ip}/h264"
    ]
    
    successful_vlc = []
    
    for i, rtsp_url in enumerate(vlc_urls, 1):
        print(f"\n{i}. Testing VLC method: {rtsp_url}")
        
        try:
            # Create VideoCapture with specific options
            cap = cv2.VideoCapture()
            
            # Set options before opening (similar to VLC)
            cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 10000)
            cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # Try to open
            success = cap.open(rtsp_url, cv2.CAP_FFMPEG)
            
            if success:
                print("   ✓ VLC-method connection successful!")
                
                # Test reading
                frame_count = 0
                for j in range(5):
                    ret, frame = cap.read()
                    if ret:
                        frame_count += 1
                        print(f"   ✓ Frame {j+1} read successfully: {frame.shape}")
                    else:
                        print(f"   ✗ Failed to read frame {j+1}")
                    time.sleep(0.1)
                
                if frame_count > 0:
                    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    
                    successful_vlc.append({
                        'url': rtsp_url,
                        'backend': 'VLC-method',
                        'resolution': f"{int(width)}x{int(height)}",
                        'fps': fps,
                        'frame_success_rate': f"{frame_count}/5"
                    })
                
                cap.release()
            else:
                print("   ✗ VLC-method failed to connect")
                cap.release()
                
        except Exception as e:
            print(f"   ✗ VLC-method error: {e}")
    
    return successful_vlc

def test_additional_urls(User, Password, ip):
    """Test additional common RTSP URL patterns"""
    
    base_url = f"rtsp://{User}:{Password}@{ip}"
    additional_urls = [
        # Common Hikvision patterns
        f"{base_url}:554/Streaming/Channels/1",
        f"{base_url}:554/Streaming/Channels/101/",
        f"{base_url}:554/Streaming/Channels/1/",
        
        # Common Dahua patterns  
        f"{base_url}:554/cam/realmonitor?channel=1&subtype=1",
        f"{base_url}/live1.sdp",
        f"{base_url}/live2.sdp",
        
        # Generic patterns
        f"{base_url}:554/live",
        f"{base_url}:554/",
        f"{base_url}/1",
        f"{base_url}/channel1",
        f"{base_url}/media/video1",
        f"{base_url}:8554/",
        
        # Different ports
        f"rtsp://{User}:{Password}@{ip}:8554/stream1",
        f"rtsp://{User}:{Password}@{ip}:7447/stream1",
        f"rtsp://{User}:{Password}@{ip}:1935/stream1"
    ]
    
    print("\n" + "=" * 70)
    print("Testing ADDITIONAL URL patterns...")
    print("=" * 70)
    
    successful_additional = []
    
    for i, url in enumerate(additional_urls, 1):
        print(f"\n{i}. Testing: {url}")
        
        try:
            cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 3000)
            cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 2000)
            
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    
                    print(f"   ✓ SUCCESS! Resolution: {int(width)}x{int(height)}, FPS: {fps}")
                    
                    successful_additional.append({
                        'url': url,
                        'backend': 'FFMPEG',
                        'resolution': f"{int(width)}x{int(height)}",
                        'fps': fps,
                        'frame_success_rate': "1/1"
                    })
                else:
                    print(f"   ✗ Connected but no frames")
            else:
                print(f"   ✗ Failed to connect")
            
            cap.release()
            
        except Exception as e:
            print(f"   ✗ Error: {e}")
    
    return successful_additional

def network_test(ip):
    """Test network connectivity"""
    print("\n" + "=" * 50)
    print("Network Connectivity Test:")
    print("=" * 50)
    
    ports_to_test = [554, 8554, 7447, 1935, 80, 8080]
    
    for port in ports_to_test:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((ip, port))
            sock.close()
            
            if result == 0:
                print(f"✓ Port {port} is accessible")
            else:
                print(f"✗ Port {port} is not accessible")
        except Exception as e:
            print(f"✗ Port {port} test error: {e}")

if __name__ == "__main__":
    os.system('cls' if os.name == 'nt' else 'clear')
    User = "root01"
    Password = "12345678" 
    ip = "192.168.1.111"

    network_test(ip)
    
    successful_main = test_rtsp_connection(User, Password, ip)

    successful_vlc = test_with_vlc_method(User, Password, ip)
    
    successful_additional = test_additional_urls(User, Password, ip)

    all_successful = successful_main + successful_vlc + successful_additional
    
    print("\n" + "=" * 70)
    print("COMPLETE SUMMARY OF ALL TESTS:")
    print("=" * 70)
    
    if all_successful:
        print(f"\n🎉 FOUND {len(all_successful)} WORKING CONNECTIONS!")
        print("\nAll successful connections:")
        
        for i, conn in enumerate(all_successful, 1):
            print(f"\n{i}. SUCCESS:")
            print(f"   URL: {conn['url']}")
            print(f"   Backend: {conn['backend']}")
            print(f"   Resolution: {conn['resolution']}")
            print(f"   FPS: {conn['fps']}")
            print(f"   Frame Success Rate: {conn['frame_success_rate']}")
        
        best_connection = max(all_successful, key=lambda x: (float(x['fps']) if x['fps'] > 0 else 0, int(x['frame_success_rate'].split('/')[0])))
        
        print(f"\n🏆 RECOMMENDED CONNECTION (Best Performance):")
        print(f"URL: {best_connection['url']}")
        print(f"Backend: {best_connection['backend']}")
        print("\nExample code:")
        backend_code = "cv2.CAP_FFMPEG" if best_connection['backend'] in ["FFMPEG", "VLC-method"] else f"cv2.CAP_{best_connection['backend']}"
        print(f"cap = cv2.VideoCapture('{best_connection['url']}', {backend_code})")
        print("cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)")
        
    else:
        print("\n❌ NO SUCCESSFUL RTSP CONNECTIONS FOUND")
        print("\nTroubleshooting suggestions:")
        print("1. Check if the camera is accessible from your network")
        print("2. Verify username/password are correct")
        print("3. Try different stream paths (/stream2, /live, etc.)")
        print("4. Check if OpenCV was compiled with FFMPEG support")
        print("   - Run: python -c \"import cv2; print(cv2.getBuildInformation())\"")
        print("5. Try installing additional codecs")
        print("6. Check camera documentation for correct RTSP URLs")
        print("7. Try accessing the camera web interface first")
        print("8. Verify the camera supports RTSP protocol")
    
    print(f"\nTest Summary:")
    print(f"Main URL patterns: {len(successful_main)} successful")
    print(f"VLC method: {len(successful_vlc)} successful")  
    print(f"Additional URL patterns: {len(successful_additional)} successful")
    print(f"Total successful connections: {len(all_successful)}")