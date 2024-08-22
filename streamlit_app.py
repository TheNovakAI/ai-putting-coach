import streamlit as st
import openai
import requests
import base64
import json

# Initialize session state for angle data
if 'angle_data' not in st.session_state:
    st.session_state['angle_data'] = None

# JavaScript to collect device orientation data
st.markdown("""
<script>
    function sendAngleData(alpha, beta, gamma) {
        var xhr = new XMLHttpRequest();
        xhr.open("POST", "/angle_data", true);
        xhr.setRequestHeader("Content-Type", "application/json");
        xhr.send(JSON.stringify({alpha: alpha, beta: beta, gamma: gamma}));
    }

    if (window.DeviceOrientationEvent) {
        window.addEventListener('deviceorientation', function(event) {
            var alpha = event.alpha;
            var beta = event.beta;
            var gamma = event.gamma;

            // Check if the device is flat
            if (Math.abs(beta) < 5 && Math.abs(gamma) < 5) {
                sendAngleData(alpha, beta, gamma);
            }
        }, true);
    }
</script>
""", unsafe_allow_html=True)

# Endpoint to receive angle data
def receive_angle_data():
    angle_data = json.loads(st.experimental_get_query_params().get('angle_data', '{}'))
    st.session_state['angle_data'] = angle_data

# Call the function to process the angle data if available
receive_angle_data()

# Streamlit UI
st.title('Golf Putt Analyzer AI')

# Step 1: Instruct the user to lay the phone flat
st.header("Step 1: Lay Your Phone Flat on the Green")
st.write("Place your phone flat on the green with the camera facing down. Ensure the phone is still, and we'll automatically capture the angle data.")

if st.button('Collect Angle Data'):
    if st.session_state['angle_data'] is not None:
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
