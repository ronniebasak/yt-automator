from dataclasses import dataclass, field
from typing import List, Optional
import xml.etree.ElementTree as ET
from xml.dom import minidom
import re


@dataclass
class Word:
    """Individual word with timing information"""
    text: str
    duration: float = 0.0  # Duration in seconds for this word


@dataclass
class VOFragment:
    """Voice-over fragment - a logical boundary that appears as subtitle text"""
    text: str
    words: List[Word] = field(default_factory=list)
    _auto_split: bool = field(default=True, init=False)  # Track if words were auto-generated
    
    def __post_init__(self):
        """Automatically split text into words if words list is empty and no Word elements were parsed"""
        if not self.words and self.text.strip() and self._auto_split:
            # Split text into words, preserving punctuation
            word_pattern = r'\S+'
            word_texts = re.findall(word_pattern, self.text)
            self.words = [Word(text=word_text) for word_text in word_texts]
    
    def set_words_from_elements(self, words: List[Word]):
        """Set words from parsed XML elements (prevents auto-splitting)"""
        self._auto_split = False
        self.words = words
    
    def set_word_durations(self, durations: List[float]):
        """Set duration for each word"""
        if len(durations) != len(self.words):
            raise ValueError(f"Duration list length ({len(durations)}) doesn't match word count ({len(self.words)})")
        
        for word, duration in zip(self.words, durations):
            word.duration = duration
    
    def get_total_duration(self) -> float:
        """Get total duration of all words in this fragment"""
        return sum(word.duration for word in self.words)


@dataclass
class VoiceOver:
    """Voice-over containing multiple fragments"""
    id: str
    fragments: List[VOFragment] = field(default_factory=list)
    start_time: float = 0.0  # When this voice-over starts (seconds)
    inset: float = 0.0      # Inset timing adjustment (seconds)  
    offset: float = 0.0     # Offset timing adjustment (seconds)
    
    def serialize_to_text(self, separator: str = " ") -> str:
        """Serialize all fragments to a single text string"""
        return separator.join(fragment.text.strip() for fragment in self.fragments)
    
    def get_duration(self) -> float:
        """Calculate total duration based on timing parameters and fragment durations"""
        base_duration = sum(fragment.get_total_duration() for fragment in self.fragments)
        return base_duration + self.inset + self.offset
    
    def get_end_time(self) -> float:
        """Calculate when this voice-over ends"""
        return self.start_time + self.get_duration()


@dataclass 
class Scene:
    """A scene containing a voice-over"""
    name: str
    title: str
    voice_over: Optional[VoiceOver] = None


@dataclass
class VideoContainer:
    """Container for all scenes in the video"""
    scenes: List[Scene] = field(default_factory=list)
    
    def get_scene_by_name(self, name: str) -> Optional[Scene]:
        """Find a scene by its name"""
        for scene in self.scenes:
            if scene.name == name:
                return scene
        return None
    
    def get_total_duration(self) -> float:
        """Get total duration of all scenes"""
        return sum(scene.voice_over.get_duration() if scene.voice_over else 0 
                  for scene in self.scenes)


class VideoScriptParser:
    """Parser for video script XML/JSX"""
    
    @staticmethod
    def parse_script(script_content: str) -> VideoContainer:
        """Parse script content and return VideoContainer
        
        ENFORCES CONSTRAINT: Word elements can only exist within VOFragment elements
        """
        # Clean up the script content - remove SCRIPT = """ wrapper if present
        content = script_content.strip()
        if content.startswith('SCRIPT = """'):
            content = content[12:]  # Remove 'SCRIPT = """'
        if content.endswith('"""'):
            content = content[:-3]  # Remove closing '"""'
        
        content = content.strip()
        
        try:
            # Parse XML
            root = ET.fromstring(content)
        except ET.ParseError as e:
            print(f"XML Parse Error: {e}")
            print("Attempting to fix common issues...")
            
            # Try to fix self-closing comment tags
            content = re.sub(r'<!--[^>]*?-->', '', content, flags=re.DOTALL)
            root = ET.fromstring(content)
        
        if root.tag != "VideoContainer":
            raise ValueError("Root element must be VideoContainer")
        
        # VALIDATE STRUCTURE: Ensure Word elements only exist within VOFragment
        VideoScriptParser._validate_structure(root)
        
        container = VideoContainer()
        
        # Parse scenes
        for scene_elem in root.findall("Scene"):
            scene = VideoScriptParser._parse_scene(scene_elem)
            container.scenes.append(scene)
        
        return container
    
    @staticmethod
    def _parse_scene(scene_elem: ET.Element) -> Scene:
        """Parse a Scene element"""
        name = scene_elem.get("name", "")
        title = scene_elem.get("title", "")
        
        scene = Scene(name=name, title=title)
        
        # Parse VoiceOver if present
        voice_over_elem = scene_elem.find("VoiceOver")
        if voice_over_elem is not None:
            scene.voice_over = VideoScriptParser._parse_voice_over(voice_over_elem)
        
        return scene
    
    @staticmethod
    def _parse_voice_over(voice_over_elem: ET.Element) -> VoiceOver:
        """Parse a VoiceOver element"""
        vo_id = voice_over_elem.get("id", "")
        voice_over = VoiceOver(id=vo_id)
        
        # Parse VOFragment elements
        for fragment_elem in voice_over_elem.findall("VOFragment"):
            fragment = VideoScriptParser._parse_vo_fragment(fragment_elem)
            voice_over.fragments.append(fragment)
        
        return voice_over
    
    @staticmethod
    def _parse_vo_fragment(fragment_elem: ET.Element) -> VOFragment:
        """Parse a VOFragment element, handling both text-only and word-level structures
        
        CONSTRAINT: Word elements can ONLY exist within VOFragment elements
        """
        # Check if this fragment contains Word elements
        word_elements = fragment_elem.findall("Word")
        
        if word_elements:
            # Parse individual Word elements (they can only exist within VOFragment)
            words = []
            word_texts = []
            
            for word_elem in word_elements:
                word_text = word_elem.text or ""
                duration = float(word_elem.get("duration", "0.0"))
                word = Word(text=word_text, duration=duration)
                words.append(word)
                word_texts.append(word_text)
            
            # Reconstruct fragment text from words
            fragment_text = " ".join(word_texts)
            
            # Create fragment with pre-parsed words
            fragment = VOFragment(text=fragment_text)
            fragment.set_words_from_elements(words)
        else:
            # Traditional text-only fragment
            fragment_text = fragment_elem.text or ""
            fragment = VOFragment(text=fragment_text)
        
        return fragment
    
    @staticmethod
    def _validate_structure(root: ET.Element):
        """Validate that Word elements only exist within VOFragment elements"""
        # Check for orphaned Word elements (not inside VOFragment)
        orphaned_words = []
        
        def check_element(elem, path=""):
            current_path = f"{path}/{elem.tag}" if path else elem.tag
            
            if elem.tag == "Word":
                # Check if parent is VOFragment
                parent_path = "/".join(current_path.split("/")[:-1])
                if not parent_path.endswith("VOFragment"):
                    orphaned_words.append(current_path)
            
            # Recursively check children
            for child in elem:
                check_element(child, current_path)
        
        check_element(root)
        
        if orphaned_words:
            raise ValueError(
                f"CONSTRAINT VIOLATION: Word elements found outside VOFragment elements at: {orphaned_words}. "
                f"Word elements can only exist within VOFragment elements."
            )


# Example usage and testing
def main():
    # Demo script with both text-only and word-level structures
    demo_script = '''
    <VideoContainer>
        <!--extremely attention grabbing first scene, title is very short, 1 or 2 words max)-->
        <Scene name="intro" title="Mind-Blowers!"> 
            <VoiceOver id="v01">
                <!-- each VOFragment is visible on subtitle text at a single glance, do not make it too verbose -->
                <VOFragment>Hey there, knowledge junkies!</VOFragment>
                <VOFragment>Strap in for some </VOFragment>
                <VOFragment>mind-bending facts </VOFragment>
                <VOFragment>that'll blow your socks off!</VOFragment>
            </VoiceOver>
        </Scene>

        <Scene name="fact-1" title="Teaspoon Mystery">
            <VoiceOver id="f-01">
                <VOFragment>Ever wonder where </VOFragment>
                <VOFragment>all the teaspoons disappear to?</VOFragment>
                <VOFragment>Scientists actually studied this!</VOFragment>
                <VOFragment>In 2004, Australian researchers </VOFragment>
                <VOFragment>investigated the great </VOFragment>
                <VOFragment>workplace teaspoon vanishing act!</VOFragment>
            </VoiceOver>
        </Scene>

        <Scene name="fact-2" title="Peace Pioneer">
            <VoiceOver id="f-02">
                <VOFragment>History making moment!</VOFragment>
                <VOFragment>Ralph Bunche smashed barriers </VOFragment>
                <VOFragment>as the first Black person </VOFragment>
                <VOFragment>to win the Nobel Peace Prize.</VOFragment>
                <VOFragment>His 1950 mediation work </VOFragment>
                <VOFragment>between Arabs and Israelis? </VOFragment>
                <VOFragment>Absolutely legendary!</VOFragment>
            </VoiceOver>
        </Scene>

        <Scene name="fact-3" title="Spartan Rules">
            <VoiceOver id="f-03">
                <VOFragment>Talk about military dedication!</VOFragment>
                <VOFragment>Spartan men couldn't live </VOFragment>
                <VOFragment>with their families until age 30!</VOFragment>
                <VOFragment>That's right - decades of </VOFragment>
                <VOFragment>military service before </VOFragment>
                <VOFragment>any family time!</VOFragment>
            </VoiceOver>
        </Scene>

        <Scene name="fact-4" title="Holy War">
            <VoiceOver id="f-04">
                <VOFragment>Get this - the U.S. literally </VOFragment>
                <VOFragment>declared war on the Mormon Church!</VOFragment>
                <VOFragment>1857 was wild when the Feds </VOFragment>
                <VOFragment>said "absolutely not" </VOFragment>
                <VOFragment>to Utah's religious laws!</VOFragment>
                <VOFragment>Church vs State showdown!</VOFragment>
            </VoiceOver>
        </Scene>

        <Scene name="fact-5" title="Hidden Jobs">
            <VoiceOver id="f-05">
                <VOFragment>Job hunting tip that'll </VOFragment>
                <VOFragment>change your life!</VOFragment>
                <VOFragment>A whopping 80% of U.S. jobs </VOFragment>
                <VOFragment>are never even advertised!</VOFragment>
                <VOFragment>It's all about who you know, </VOFragment>
                <VOFragment>not what you apply for!</VOFragment>
            </VoiceOver>
        </Scene>

        <Scene name="fact-6" title="Deadly Commute">
            <VoiceOver id="f-06">
                <VOFragment>This will shock you!</VOFragment>
                <VOFragment>In 2015 alone, </VOFragment>
                <VOFragment>NINE people died EVERY DAY </VOFragment>
                <VOFragment>just commuting on </VOFragment>
                <VOFragment>Mumbai's local trains!</VOFragment>
                <VOFragment>Makes your traffic jam </VOFragment>
                <VOFragment>seem pretty tame, huh?</VOFragment>
            </VoiceOver>
        </Scene>

        <Scene name="fact-7" title="Tree Naps">
            <VoiceOver id="f-07">
                <VOFragment>Trees are basically </VOFragment>
                <VOFragment>the ultimate nappers!</VOFragment>
                <VOFragment>Science proves they "sleep" at night, </VOFragment>
                <VOFragment>chilling out their branches </VOFragment>
                <VOFragment>after dark and </VOFragment>
                <VOFragment>perking up before sunrise!</VOFragment>
            </VoiceOver>
        </Scene>

        <Scene name="fact-8" title="SPF Exposed">
            <VoiceOver id="f-08">
                <VOFragment>Your sunscreen is lying to you!</VOFragment>
                <VOFragment>SPF is totally nonlinear!</VOFragment>
                <VOFragment>SPF 15 blocks 93%, </VOFragment>
                <VOFragment>SPF 30 blocks 97%, </VOFragment>
                <VOFragment>and SPF 50? Just 98%!</VOFragment>
                <VOFragment>That higher number isn't </VOFragment>
                <VOFragment>as magical as you think!</VOFragment>
            </VoiceOver>
        </Scene>

        <Scene name="fact-9" title="Texas Limit">
            <VoiceOver id="f-09">
                <VOFragment>Texas has some </VOFragment>
                <VOFragment>interesting priorities!</VOFragment>
                <VOFragment>It's actually illegal to own </VOFragment>
                <VOFragment>six or more dildos there!</VOFragment>
                <VOFragment>Five? You're good!</VOFragment>
                <VOFragment>Six? You're a criminal!</VOFragment>
            </VoiceOver>
        </Scene>

        <Scene name="fact-10" title="Word Power">
            <VoiceOver id="f-10">
                <VOFragment>Your brain is a dictionary!</VOFragment>
                <VOFragment>By age 20, the average </VOFragment>
                <VOFragment>English-speaking American </VOFragment>
                <VOFragment>knows a staggering </VOFragment>
                <VOFragment>42,000 dictionary words!</VOFragment>
                <VOFragment>No wonder you're so </VOFragment>
                <VOFragment>impressively articulate!</VOFragment>
            </VoiceOver>
        </Scene>
    </VideoContainer>
    '''
    
    parser = VideoScriptParser()
    
    print("=== Video Script Parser Demo ===")
    container = parser.parse_script(demo_script)
    
    print(f"Total scenes: {len(container.scenes)}")
    print(f"Total duration: {container.get_total_duration():.1f}s")
    print()
    
    for scene in container.scenes:
        print(f"Scene: {scene.name} - '{scene.title}'")
        if scene.voice_over:
            print(f"  Voice Over ID: {scene.voice_over.id}")
            print(f"  Full Text: {scene.voice_over.serialize_to_text()}")
            
            for i, fragment in enumerate(scene.voice_over.fragments):
                print(f"    Fragment {i+1}: '{fragment.text.strip()}'")
                if fragment._auto_split:
                    print(f"      Auto-split words: {[word.text for word in fragment.words]}")
                else:
                    print(f"      Parsed words with durations:")
                    for word in fragment.words:
                        print(f"        '{word.text}' ({word.duration}s)")
                    print(f"      Fragment duration: {fragment.get_total_duration()}s")
        print()
    
    print("✅ Constraint enforced: Word elements can only exist within VOFragment elements")



if __name__ == "__main__":
    main()