import base64
import os
from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from config import API_KEY

class ViolatorAnalysis(BaseModel):
    is_using_phone: bool = Field(description="True if the person in the image is holding, looking at, or actively using a mobile phone. False otherwise.")
    gender: str = Field(description="Gender of the person. Must be 'male', 'female', or 'unknown'.")
    direction: str = Field(description="Direction of the person on the stairs. Must be 'up' (walking up), 'down' (walking down), or 'unknown'.")
    confidence: float = Field(description="Confidence score of the decision between 0.0 and 1.0.")
    explanation: str = Field(description="Brief explanation of the visual evidence observed in the image.")

def encode_image(image_path: str) -> str:
    """Encodes a local image to base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

class ImageAnalyzer:
    def __init__(self):
        self.api_key = API_KEY
        
        if not self.api_key:
            print("[WARNING] API_KEY not found in configurations. Running in DEMO/MOCK mode.")
            self.model = None
        else:
            try:
                self.model = ChatOpenAI(
                    model="google/gemini-2.5-flash-lite",
                    openai_api_base="https://openrouter.ai/api/v1",
                    api_key=self.api_key,
                    temperature=0.1
                ).with_structured_output(ViolatorAnalysis)
                print("[INFO] Langchain Gemini 2.5 Flash analyzer successfully initialized.")
            except Exception as e:
                print(f"[ERROR] Failed to initialize model: {e}. Falling back to MOCK mode.")
                self.model = None

    def analyze_cropped_image(self, image_path: str) -> ViolatorAnalysis:
        """
        Analyzes a cropped person image to detect phone usage, gender, and direction.
        Returns a ViolatorAnalysis object.
        """
        if self.model is None:
            import random
            print(f"[DEMO MODE] Mock-analyzing image: {image_path}")
            genders = ["male", "female"]
            directions = ["up", "down"]
            return ViolatorAnalysis(
                is_using_phone=True,
                gender=random.choice(genders),
                direction=random.choice(directions),
                confidence=0.91,
                explanation="[MOCK] Detected phone in left hand while walking up the stairs (API Key not set)."
            )
            
        try:
            base64_image = encode_image(image_path)
            
            prompt = (
                "Analyze the attached image of a person captured on a staircase camera.\n"
                "Determine and extract the following details:\n"
                "1. If they are actively holding, using, or looking at a mobile phone (is_using_phone: true/false).\n"
                "2. Their gender (gender: 'male', 'female', or 'unknown').\n"
                "3. Their walking direction relative to the staircase (direction: 'up' if walking up, 'down' if walking down, or 'unknown').\n\n"
                "Rely strictly on visual evidence in this cropped photo. Explain clearly what you see in the explanation field."
            )
            
            message = HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                    }
                ]
            )
            
            result = self.model.invoke([message])
            return result
        except Exception as e:
            print(f"[ERROR] API request failed: {e}. Returning fallback analysis.")
            return ViolatorAnalysis(
                is_using_phone=False,
                gender="unknown",
                direction="unknown",
                confidence=0.0,
                explanation=f"Error occurred during API analysis: {str(e)}"
            )

if __name__ == "__main__":
    analyzer = ImageAnalyzer()
    test_img = "test_image.jpg"
    with open(test_img, "wb") as f:
        f.write(b"fake image data")
        
    try:
        result = analyzer.analyze_cropped_image(test_img)
        print("Analysis Result:")
        print(f"  Phone Detected: {result.is_using_phone}")
        print(f"  Gender:         {result.gender}")
        print(f"  Direction:      {result.direction}")
        print(f"  Confidence:     {result.confidence}")
        print(f"  Explanation:    {result.explanation}")
    finally:
        import os
        if os.path.exists(test_img):
            os.remove(test_img)
