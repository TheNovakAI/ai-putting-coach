import streamlit as st
import openai
import requests
import base64
import json

# Initialize session state for angle data
if 'angle_data' not in st.session_state:
    st.session_state['angle_data'] = {}

# JavaScript to collect device orientation data and send it to Streamlit
st.markdown("""
<script>
    let angleData = {alpha: 0, beta: 0, gamma: 0};

    function sendAngleData() {
        const xhr = new XMLHttpRequest();
        xhr.open("POST", "http://localhost:8501/angle_data", true);
        xhr.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
        xhr.send(JSON.stringify(angleData));
    }

    if (window.DeviceOrientationEvent) {
        window.addEventListener('deviceorientation', function(event) {
            angleData.alpha = event.alpha; // Rotation around Z axis (0 to 360 degrees)
            angleData.beta = event.beta;   // Rotation around X axis (-180 to 180 degrees)
            angleData.gamma = event.gamma; // Rotation around Y axis (-90 to 90 degrees)

            // Check if the device is flat
            if (Math.abs(angleData.beta) < 5 && Math.abs(angleData.gamma) < 5) {
                sendAngleData();
            }
        }, true);
    }
</script>
""", unsafe_allow_html=True)

# Endpoint to receive angle data from JavaScript
if st._is_running_with_streamlit:
    from streamlit.server.server import Server

    @st.experimental_singleton
    def get_server():
        return Server.get_current()._session_mgr

    # Get the session manager instance
    server = get_server()

    # Hook into the WebSocketHandler to receive the POST request
    server._websocket_handler_class._overrides['angle_data'] = lambda handler, message: handler._callback(
        json.loads(message['data'])
    )

    def handle_angle_data(data):
        st.session_state['angle_data'] = data

    server._websocket_handler_class._overrides['angle_data'] = handle_angle_data

# Streamlit UI
st.title('Golf Putt Analyzer AI')

# Step 1: Instruct the user to lay the phone flat
st.header("Step 1: Lay Your Phone Flat on the Green")
st.write("Place your phone flat on the green with the camera facing down. Ensure the phone is still, and we'll automatically capture the angle data.")

if st.button('Collect Angle Data'):
    if st.session_state['angle_data']:
        st.success("Angle data collected successfully!")
        st.write("Collected Angle Data:", st.session_state['angle_data'])
    else:
        st.error("Please ensure your phone is laying flat and still.")

# Step 2: Tilt the phone and capture the image
st.header("Step 2: Tilt Your Phone Towards the Hole")
st.write("Tilt your phone 90 degrees so that the camera is facing the hole, then take a picture.")

uploaded_file = st.camera_input("Take a picture")

if uploaded_file is not None:
    st.image(uploaded_file, caption="Captured Image", use_column_width=True)

    if st.button('Analyze Putt'):
        # Convert the uploaded file to base64
        def encode_image(image):
            return base64.b64encode(image.getvalue()).decode('utf-8')

        base64_image = encode_image(uploaded_file)
        st.write("Analyzing your putt...")

        # Prepare the API request
        api_key = st.secrets["openai_api_key"]
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        payload = {
            "model": "gpt-4-vision-preview",
            "messages": [
                {
                    "role": "user",
                    "content": f"Analyze this putt. Consider the angle data: {st.session_state['angle_data']}."
                },
                {
                    "role": "user",
                    "content": {
                        "type": "image_url",
                        "image_url": f"data:image/jpeg;base64,{base64_image}"
                    }
                }
            ],
            "max_tokens": 300
        }

        # Send request to OpenAI API
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        advice = response.json()

        # Display the advice
        st.write("Putt Analysis: ")
        st.write(advice['choices'][0]['message']['content'])
