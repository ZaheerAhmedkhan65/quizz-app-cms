import PyPDF2
import re
import random
from collections import defaultdict
import nltk
from nltk.tokenize import sent_tokenize
from transformers import pipeline

# Download required NLTK data
nltk.download('punkt')

class MCQGenerator:
    def __init__(self):
        self.question_generator = pipeline("text2text-generation", model="mrm8488/t5-base-finetuned-question-generation-ap")
        
    def extract_text_from_pdf(self, pdf_path):
        """Extract text from PDF file"""
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            print(f"Error reading PDF: {e}")
        return text
    
    def preprocess_text(self, text):
        """Clean and preprocess extracted text"""
        # Remove extra whitespaces
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.\,\?\!]', '', text)
        return text.strip()
    
    def identify_topics(self, text):
        """Identify different topics in the text"""
        # Simple topic identification based on headings and keywords
        topics = defaultdict(list)
        current_topic = "General"
        
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            # Detect topic headers (usually in caps, bold, or numbered)
            if (len(line) < 100 and 
                (line.isupper() or 
                 re.match(r'^(Topic|Chapter|Section|Q\s*No)', line, re.IGNORECASE) or
                 re.match(r'^\d+\.', line))):
                current_topic = line
            elif len(line) > 20:  # Meaningful content
                topics[current_topic].append(line)
        
        return topics
    
    def generate_mcqs_from_sentence(self, sentence, num_options=4):
        """Generate MCQs from a single sentence"""
        try:
            # Use the question generation model
            result = self.question_generator(sentence, max_length=100, num_return_sequences=1)
            if result:
                generated_question = result[0]['generated_text']
                
                # Create dummy options (in a real scenario, you'd generate meaningful distractors)
                options = [
                    "Correct Answer (would need context analysis)",
                    "Incorrect Option 1",
                    "Incorrect Option 2", 
                    "Incorrect Option 3"
                ]
                
                return {
                    'question': generated_question,
                    'options': options,
                    'correct_answer': 0  # This would need proper analysis
                }
        except Exception as e:
            print(f"Error generating question: {e}")
        
        return None
    
    def create_mcqs_from_topics(self, topics, mcqs_per_topic=10):
        """Create MCQs for each identified topic"""
        all_mcqs = {}
        
        for topic, content in topics.items():
            if len(content) < 3:  # Skip topics with very little content
                continue
                
            topic_mcqs = []
            combined_content = " ".join(content[:500])  # Limit content length
            
            # Split into sentences
            sentences = sent_tokenize(combined_content)
            
            # Select random sentences to generate questions from
            selected_sentences = random.sample(
                [s for s in sentences if len(s) > 30], 
                min(mcqs_per_topic, len(sentences))
            )
            
            for sentence in selected_sentences:
                mcq = self.generate_mcqs_from_sentence(sentence)
                if mcq:
                    topic_mcqs.append(mcq)
            
            if topic_mcqs:
                all_mcqs[topic] = topic_mcqs
        
        return all_mcqs
    
    def save_mcqs_to_file(self, mcqs, output_file):
        """Save generated MCQs to a text file"""
        with open(output_file, 'w', encoding='utf-8') as f:
            for topic, topic_mcqs in mcqs.items():
                f.write(f"\n{'='*50}\n")
                f.write(f"TOPIC: {topic}\n")
                f.write(f"{'='*50}\n\n")
                
                for i, mcq in enumerate(topic_mcqs, 1):
                    f.write(f"Question #{i}\n")
                    f.write(f"{mcq['question']}\n\n")
                    f.write("Select the correct option:\n")
                    
                    for j, option in enumerate(mcq['options']):
                        f.write(f"- [ ] {option}\n")
                    
                    f.write(f"\nCorrect Answer: Option {mcq['correct_answer'] + 1}\n")
                    f.write("-" * 40 + "\n\n")
    
    def generate_from_pdf(self, pdf_path, output_file, mcqs_per_topic=10):
        """Main function to generate MCQs from PDF"""
        print("Extracting text from PDF...")
        text = self.extract_text_from_pdf(pdf_path)
        
        if not text:
            print("No text extracted from PDF")
            return
        
        print("Preprocessing text...")
        cleaned_text = self.preprocess_text(text)
        
        print("Identifying topics...")
        topics = self.identify_topics(cleaned_text)
        
        print(f"Found {len(topics)} topics")
        
        print("Generating MCQs...")
        all_mcqs = self.create_mcqs_from_topics(topics, mcqs_per_topic)
        
        print("Saving MCQs to file...")
        self.save_mcqs_to_file(all_mcqs, output_file)
        
        total_mcqs = sum(len(mcqs) for mcqs in all_mcqs.values())
        print(f"Generated {total_mcqs} MCQs saved to {output_file}")

# Alternative simpler approach for template-based generation
class TemplateMCQGenerator:
    def __init__(self):
        self.question_templates = [
            "What is the main purpose of {concept}?",
            "Which of the following best describes {concept}?",
            "What are the key components of {concept}?",
            "How does {concept} work in information security?",
            "What is the primary function of {concept}?",
            "Which protocol is used for {concept}?",
            "What are the main challenges in implementing {concept}?",
            "How is {concept} different from {related_concept}?",
            "What security controls are associated with {concept}?",
            "Why is {concept} important in cybersecurity?"
        ]
    
    def extract_concepts(self, text):
        """Extract key concepts from text using simple pattern matching"""
        # Look for capitalized terms, acronyms, and technical terms
        concepts = set()
        
        # Find acronyms (2-5 capital letters)
        acronyms = re.findall(r'\b[A-Z]{2,5}\b', text)
        concepts.update(acronyms)
        
        # Find technical terms (words that appear multiple times and are capitalized)
        words = re.findall(r'\b[A-Z][a-z]+\b', text)
        word_freq = defaultdict(int)
        for word in words:
            if len(word) > 3:  # Avoid short common words
                word_freq[word] += 1
        
        # Add frequent technical terms
        for word, freq in word_freq.items():
            if freq > 2:
                concepts.add(word)
        
        return list(concepts)
    
    def generate_template_mcqs(self, concepts, num_questions=10):
        """Generate MCQs using templates"""
        mcqs = []
        
        for i in range(min(num_questions, len(concepts))):
            concept = concepts[i]
            template = random.choice(self.question_templates)
            
            # Simple placeholder replacement
            question = template.format(
                concept=concept,
                related_concept=random.choice([c for c in concepts if c != concept])
            )
            
            # Generate options (in real scenario, these would be meaningful)
            options = [
                f"Correct definition related to {concept}",
                f"Incorrect option 1 about {concept}",
                f"Incorrect option 2 about {concept}",
                f"Incorrect option 3 about {concept}"
            ]
            
            mcqs.append({
                'question': question,
                'options': options,
                'correct_answer': 0
            })
        
        return mcqs

def main():
    # Initialize generators
    advanced_generator = MCQGenerator()
    template_generator = TemplateMCQGenerator()
    
    # Path to your PDF file
    pdf_path = "cs205_handout.pdf"  # Replace with your PDF path
    output_file = "generated_mcqs.txt"
    
    try:
        # Try advanced generation first
        print("Attempting advanced MCQ generation...")
        advanced_generator.generate_from_pdf(pdf_path, output_file, mcqs_per_topic=5)
        
    except Exception as e:
        print(f"Advanced generation failed: {e}")
        print("Falling back to template-based generation...")
        
        # Fallback to template-based approach
        text = advanced_generator.extract_text_from_pdf(pdf_path)
        if text:
            cleaned_text = advanced_generator.preprocess_text(text)
            concepts = template_generator.extract_concepts(cleaned_text)
            
            all_mcqs = {}
            topics = advanced_generator.identify_topics(cleaned_text)
            
            for topic in list(topics.keys())[:10]:  # Limit to first 10 topics
                topic_mcqs = template_generator.generate_template_mcqs(concepts, 3)
                if topic_mcqs:
                    all_mcqs[topic] = topic_mcqs
            
            advanced_generator.save_mcqs_to_file(all_mcqs, output_file)
            total = sum(len(mcqs) for mcqs in all_mcqs.values())
            print(f"Generated {total} template-based MCQs")

if __name__ == "__main__":
    main()