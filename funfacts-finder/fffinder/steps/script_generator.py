import openai
import os
import dotenv
from fffinder.config import settings
from typing import List
import orjson as json
import textwrap
from fffinder.xml_block_parser import extract_xml_from_text

dotenv.load_dotenv()

assert os.getenv("OPENROUTER_API_KEY", "UNDEFINED") != "UNDEFINED", Exception(
    "OpenRouter API Key Undefined"
)

client = openai.OpenAI(
    base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPENROUTER_API_KEY")
)

# FACT_DIR = "fact-chunks"


SYSPROMPT = """
You are passed a list of 10 fun facts, create a narrative script that adheres strictly to the JSX/XML structure:

Make the wording spicy, catchy and purely conversational!

{FAXXX}
----
<VideoContainer>
    <!--extremely attention grabbing first scene, title is very short, 1 or 2 words max)-->
    <Scene name="intro" title="Scene Title!"> 
        <VoiceOver id="v01">
            <!-- each VOFragment is visible on subtitle text at a single glance, do not make it too verbose -->
            <VOFragment>Hello HuffleDoodles! </VOFragment>
            <VOFragment>Make the intro </VOFragment>
            <VOFragment>extraordinarily catchy </VOFragment>
            <VOFragment>No rules, all vibes!</VOFragment>
        </VoiceOver>
    </Scene>

    <Scene name="fact-1" title="Birds!">
        <VoiceOver id="f-01">
            <VOFragment>Birds can fly</VOFragment>
            <VOFragment>High in the sky</VOFragment>
        </VoiceOver>
    </Scene>
</VideoContainer>
"""




def get_facts(_factId: str):
    factId = _factId.zfill(settings.MAX_DIGITS_CHUNK)
    fd = open(
        os.path.join(settings.CHUNKS_DIRECTORY, f"{settings.CHUNK_PREFIX}{factId}.json")
    ).read()
    return json.loads(fd)



def get_script(facts: List[str]):
    resp = client.chat.completions.create(
        # model="deepseek/deepseek-r1-0528",
        model="z-ai/glm-4.5",
        messages= [
            {
                "role": "system",
                "content": "You are an excellent marketer, write excellent copy and always return responses in the XML/JSX syntax as requested"
            },
            {
                "role": "user",
                "content": textwrap.dedent(SYSPROMPT.replace("{FAXXX}", str(facts))).strip()
            },
        ],
        temperature=0.7
    )
    response = resp.choices[0].message.content
    print(response)

    xtracted = extract_xml_from_text(response or "")
    return xtracted

####

fax = get_facts("48")
print(fax)

scrypt = get_script(fax)

print(scrypt)
