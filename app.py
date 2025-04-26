from flask import Flask, render_template, request, jsonify
import os
import requests
import json
import time
import re
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("law_assistant.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("IndianLawAssistant")

app = Flask(__name__)

# In production, use environment variables for security
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Comprehensive fallback responses for common legal questions in India
FALLBACK_RESPONSES = {
    "rights if arrested": {
        "keywords": ["arrest", "detained", "police custody", "rights when arrested", "police rights"],
        "response": """
        <h3>Rights When Arrested in India</h3>
        
        Under Indian law, you have the following rights if arrested:
        
        1. <b>Right to know reason for arrest</b> (Section 50 of CrPC, 1973)
        2. <b>Right to meet a lawyer</b> (Article 22(1) of Constitution)
        3. <b>Right to be produced before magistrate within 24 hours</b> (Article 22(2))
        4. <b>Right to inform family/friend</b> about arrest (DK Basu guidelines, Supreme Court)
        5. <b>Right against self-incrimination</b> (Article 20(3))
        6. <b>Right to medical examination</b> (Section 54 of CrPC)
        7. <b>Right to free legal aid</b> (Article 39A and Section 304 of CrPC)
        8. <b>Right to silence</b> (Article 20(3))
        9. <b>Right to humane treatment</b> (Article 21)
        
        <i>Note: D.K. Basu v. State of West Bengal (1997) guidelines are now part of CrPC Sections 41A-41D and 60A.</i>
        """
    },
    
    "rti act": {
        "keywords": ["rti", "right to information", "information act", "public information", "file rti"],
        "response": """
        <h3>Right to Information (RTI) Act, 2005</h3>
        
        <b>Key Provisions:</b>
        
        1. <b>Filing procedure:</b> Submit application to Public Information Officer (PIO) with fee (Section 6)
        2. <b>Response time:</b> 30 days standard; 48 hours for life/liberty matters (Section 7)
        3. <b>Fee:</b> Application fee Rs. 10; additional charges for information formats
        4. <b>Exemptions:</b> National security, trade secrets, privacy (Section 8); copyright (Section 9)
        5. <b>Appeals:</b> First appeal to departmental officer; Second appeal to Information Commission
        6. <b>Penalties:</b> Up to Rs. 25,000 for wrongful denial of information (Section 20)
        
        <i>Update: RTI (Amendment) Act, 2019 modified terms and conditions of Information Commissioners.</i>
        
        <i>Key case: CBSE v. Aditya Bandopadhyay (2011) - RTI shouldn't overwhelm public authorities.</i>
        """
    },
    
    "fundamental rights": {
        "keywords": ["fundamental rights", "constitution", "article 14", "article 19", "article 21", "basic rights"],
        "response": """
        <h3>Fundamental Rights in India</h3>
        
        Constitution of India guarantees these Fundamental Rights (Part III):
        
        1. <b>Right to Equality (Articles 14-18):</b>
           - Equality before law (Art. 14)
           - Non-discrimination (Art. 15)
           - Equal opportunity (Art. 16)
           - Abolition of untouchability (Art. 17)
        
        2. <b>Right to Freedom (Articles 19-22):</b>
           - Six freedoms: speech, assembly, association, movement, residence, profession (Art. 19)
           - Protection against arbitrary conviction (Art. 20)
           - Right to life and personal liberty (Art. 21)
           - Right to education (Art. 21A)
           - Protection against detention (Art. 22)
        
        3. <b>Right against Exploitation (Articles 23-24)</b>
        
        4. <b>Right to Freedom of Religion (Articles 25-28)</b>
        
        5. <b>Cultural and Educational Rights (Articles 29-30)</b>
        
        6. <b>Right to Constitutional Remedies (Article 32)</b>
        
        <i>Landmark case: Kesavananda Bharati v. State of Kerala (1973) established that fundamental rights are part of Constitution's "basic structure".</i>
        """
    },
    
    "consumer protection": {
        "keywords": ["consumer", "consumer rights", "product liability", "consumer complaint", "consumer forum"],
        "response": """
        <h3>Consumer Protection Act, 2019</h3>
        
        1. <b>Consumer Definition:</b> Anyone who buys goods/services for consideration (Section 2(7))
        
        2. <b>Consumer Rights:</b>
           - Protection against hazardous products/services
           - Information about quality, quantity, potency
           - Access to variety of goods at competitive prices
           - Redressal against unfair practices
           
        3. <b>Three-Tier Redressal System:</b>
           - District Commission (up to ₹1 crore)
           - State Commission (₹1-10 crore)
           - National Commission (above ₹10 crore)
        
        4. <b>Key Features:</b>
           - Central Consumer Protection Authority (CCPA)
           - Product liability actions
           - Penalties for misleading advertisements
           - E-commerce regulations
           - Mediation provisions
           
        <i>Important case: Lucknow Development Authority v. M.K. Gupta (1994) brought statutory bodies under consumer protection laws.</i>
        """
    },
    
    "inheritance laws": {
        "keywords": ["inheritance", "property rights", "succession", "heir", "will", "property inheritance"],
        "response": """
        <h3>Inheritance Laws in India</h3>
        
        Inheritance is governed by religion-based personal laws:
        
        1. <b>Hindu Succession Act, 1956 (amended 2005):</b>
           - Equal rights to daughters in ancestral property (Section 6)
           - Separate rules for male and female succession
           - Women have full ownership rights to property (Section 14)
        
        2. <b>Muslim Personal Law:</b>
           - Sunni: Son receives twice daughter's share
           - Shia: More complex calculations based on relationship
           - Will (Wasiyat): Can bequeath up to 1/3rd of property
        
        3. <b>Indian Succession Act, 1925:</b>
           - Applies to Christians, Parsis, others
           - Detailed rules for intestate and testamentary succession
        
        <i>Landmark case: Vineeta Sharma v. Rakesh Sharma (2020) - Supreme Court confirmed daughters have equal coparcenary rights in Hindu joint family property regardless of when father died.</i>
        """
    },
    
    "divorce": {
        "keywords": ["divorce", "mutual consent", "alimony", "child custody", "judicial separation", "marriage dissolution"],
        "response": """
        <h3>Divorce Laws in India</h3>
        
        Different personal laws govern divorce procedures:
        
        1. <b>Hindu Marriage Act, 1955:</b>
           - Grounds: Adultery, cruelty, desertion, conversion, mental illness, etc. (Section 13)
           - Mutual consent divorce: 6-18 month cooling period after filing (Section 13B)
           - One year separation required before filing
        
        2. <b>Muslim Personal Law:</b>
           - Talaq-ul-Sunnat (revocable)
           - Triple talaq criminalized by Muslim Women Act, 2019
           - Khula (wife-initiated divorce)
           - Mubarat (mutual consent)
        
        3. <b>Special Marriage Act, 1954:</b>
           - For inter-religious and civil marriages
           - Similar grounds to Hindu Marriage Act
        
        4. <b>Indian Divorce Act, 1869:</b>
           - For Christians (amended 2001 for gender equality)
        
        <i>Key case: Naveen Kohli v. Neelu Kohli (2006) - Supreme Court recommended "irretrievable breakdown" as divorce ground.</i>
        """
    },
    
    "cyber crime": {
        "keywords": ["cyber crime", "hacking", "online fraud", "digital crime", "it act", "cybersecurity"],
        "response": """
        <h3>Cyber Crime Laws in India</h3>
        
        1. <b>Information Technology Act, 2000 (amended 2008):</b>
           - Unauthorized access/data theft (Section 43) - Civil liability
           - Computer-related offenses/hacking (Section 66)
           - Identity theft (Section 66C)
           - Cheating by impersonation (Section 66D)
           - Privacy violation (Section 66E)
           - Cyber terrorism (Section 66F)
           - Publishing obscene material (Section 67)
           - Child pornography (Section 67B)
        
        2. <b>IPC provisions:</b>
           - Cheating (Section 420)
           - Forgery (Section 463-465)
           - Defamation (Section 499)
           - Criminal intimidation (Section 503)
        
        3. <b>Reporting:</b> Local police stations, cyber cells, or cybercrime.gov.in
        
        <i>Note: Section 66A (offensive messages) was struck down in Shreya Singhal v. Union of India (2015)</i>
        
        <i>Key case: NASSCOM v. Ajay Sood (2005) recognized phishing as combining trademark infringement and cyber fraud.</i>
        """
    },
    
    "labour laws": {
        "keywords": ["labour laws", "employee rights", "industrial dispute", "minimum wage", "pf", "esi", "working hours"],
        "response": """
        <h3>Labour Laws in India</h3>
        
        India has consolidated 29 labour laws into four labour codes:
        
        1. <b>Code on Wages, 2019:</b>
           - Universal minimum wage
           - Timely payment of wages and bonuses
           - Gender-neutral remuneration
        
        2. <b>Industrial Relations Code, 2020:</b>
           - Redefines "strike" to include mass casual leave
           - 14-day notice period for strikes/lockouts
           - Easier retrenchment for firms with up to 300 workers
        
        3. <b>Occupational Safety Code, 2020:</b>
           - Single establishment registration
           - Women permitted in night shifts with safeguards
           - Annual health check-ups for employees
        
        4. <b>Social Security Code, 2020:</b>
           - Universal social security coverage
           - Gratuity for fixed-term employees
           - Benefits for gig/platform workers
        
        <i>Note: These codes have been passed but implementation rules are still being finalized by states.</i>
        
        <i>Key case: Visakha v. State of Rajasthan (1997) led to Sexual Harassment at Workplace Act, 2013.</i>
        """
    },
    
    "criminal procedure": {
        "keywords": ["criminal procedure", "fir", "bail", "arrest procedure", "criminal case", "ipc", "crpc"],
        "response": """
        <h3>Criminal Procedure in India</h3>
        
        Governed by Criminal Procedure Code (CrPC), 1973:
        
        1. <b>FIR (First Information Report):</b>
           - Section 154: Police must register FIR for cognizable offenses
           - Can be filed by victim or witness
           - If police refuse, complaint can be sent to Superintendent of Police (Section 154(3))
        
        2. <b>Arrest Procedure:</b>
           - Section 41: Conditions for arrest without warrant
           - Section 41A: Notice of appearance for investigation
           - Section 46: Method of arrest (no unnecessary restraint)
        
        3. <b>Bail Provisions:</b>
           - Section 436: Bailable offenses - right to bail
           - Section 437: Non-bailable offenses - court discretion
           - Section 438: Anticipatory bail
           - Section 439: Special powers of High Court/Sessions Court
        
        4. <b>Trial Process:</b>
           - Sections 225-237: Sessions trials
           - Sections 238-250: Warrant trials
           - Sections 251-259: Summons trials
        
        <i>Landmark case: Arnesh Kumar v. State of Bihar (2014) - Supreme Court guidelines to prevent unnecessary arrests.</i>
        """
    },
    
    "property laws": {
        "keywords": ["property", "real estate", "land", "registration", "property dispute", "transfer of property"],
        "response": """
        <h3>Property Laws in India</h3>
        
        1. <b>Transfer of Property Act, 1882:</b>
           - Regulates transfer of immovable property (Section 5)
           - Rules for sales, mortgages, leases, gifts
           - Requirements for valid transfers (Section 54)
        
        2. <b>Registration Act, 1908:</b>
           - Mandatory registration for property transfers above Rs. 100 (Section 17)
           - Time limit: 4 months from execution (Section 23)
        
        3. <b>Real Estate (Regulation and Development) Act, 2016:</b>
           - Registration of real estate projects (Section 3)
           - Establishes Real Estate Regulatory Authority
           - Mandates developer disclosures
           - Penalties for violations
        
        4. <b>Land Acquisition Act, 2013:</b>
           - Social impact assessment mandatory
           - Compensation at 2-4 times market value
           - Consent requirements: 70-80% of landowners
        
        <i>State Variations:</i> Property laws have state-specific amendments and local regulations.
        
        <i>Key case: Suraj Lamp & Industries v. State of Haryana (2012) - Supreme Court declared sale through General Power of Attorney without proper registration invalid.</i>
        """
    },
    
    "family laws": {
        "keywords": ["family law", "marriage", "adoption", "custody", "guardianship", "maintenance"],
        "response": """
        <h3>Family Laws in India</h3>
        
        1. <b>Marriage Laws:</b>
           - Hindu Marriage Act, 1955 (for Hindus, Buddhists, Jains, Sikhs)
           - Special Marriage Act, 1954 (inter-religious/civil marriages)
           - Muslim Personal Law (Shariat) Application Act, 1937
           - Indian Christian Marriage Act, 1872
           - Parsi Marriage and Divorce Act, 1936
        
        2. <b>Adoption Laws:</b>
           - Hindu Adoption and Maintenance Act, 1956
           - Juvenile Justice Act, 2015 (secular adoption)
           - Guidelines for Adoption from India, 2022
        
        3. <b>Child Custody:</b>
           - Guardian and Wards Act, 1890 (principal law)
           - Hindu Minority and Guardianship Act, 1956
           - "Best interest of child" principle (Supreme Court rulings)
        
        4. <b>Maintenance:</b>
           - Section 125 CrPC (universal application)
           - Hindu Adoption and Maintenance Act (for Hindus)
           - Muslim Women (Protection of Rights on Divorce) Act, 1986
        
        <i>Landmark case: ABC v. State (NCT of Delhi) (2015) - Unwed mother can be sole guardian without disclosing father's identity.</i>
        """
    }
}

@app.route('/')
def index():
    return render_template('index.html')

def find_fallback_response(query):
    """Find the best matching fallback response for a query"""
    query = query.lower()
    
    for topic, data in FALLBACK_RESPONSES.items():
        for keyword in data["keywords"]:
            if keyword.lower() in query:
                logger.info(f"Using fallback for topic: {topic}")
                return data["response"]
    
    return None

@app.route('/query', methods=['POST'])
def process_query():
    data = request.json
    user_query = data.get('query', '').strip()
    
    if not user_query:
        return jsonify({"response": "Please provide a query about Indian law."})
    
    logger.info(f"Received query: {user_query}")
    
    # Try fallback response first (more efficient)
    fallback_response = find_fallback_response(user_query)
    if fallback_response:
        return jsonify({"response": fallback_response})
    
    # Use Gemini API if no fallback available
    try:
        for attempt in range(3):  # 3 retry attempts
            try:
                response = get_legal_response(user_query)
                return jsonify({"response": response})
            except Exception as e:
                logger.warning(f"API attempt {attempt+1} failed: {str(e)}")
                if attempt < 2:  # Only wait if we're going to retry
                    time.sleep(2)
                else:
                    raise
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        
        # Generic fallback for API failures
        fallback = """
        <h3>Information Temporarily Unavailable</h3>
        
        I'm currently unable to retrieve specific information about your legal query.
        
        <b>For accurate legal information in India, please consider:</b>
        
        1. Consulting a practicing advocate
        2. Visiting official websites:
           - India Code (indiacode.nic.in) for legislation
           - Indian Kanoon (indiankanoon.org) for case laws
           - e-Courts (ecourts.gov.in) for case status
        3. Contacting legal aid services through NALSA
        
        <i>Disclaimer: This information is for educational purposes only and does not constitute legal advice.</i>
        """
        return jsonify({"response": fallback})

def get_legal_response(query):
    """Get response from Gemini API with an improved legal prompt"""
    endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
    
    # Improved prompt for more accurate legal information
    legal_prompt = f"""
    As an Indian legal expert, provide precise, accurate information on:
    
    "{query}"
    
    Requirements:
    1. Focus exclusively on Indian law and applicable sections
    2. Structure response with HTML formatting (<h3>, <b>, <i>)
    3. Include specific sections of relevant legislation (Acts/Codes)
    4. Reference key Supreme Court/High Court judgments with years
    5. Explain complex legal concepts in simple, accessible language
    6. Address recent amendments or pending changes if relevant
    7. Limit response to 3-5 key points with concise explanations
    8. Note regional/state differences where applicable
    
    Keep answers factual, clear, and focused on established legal principles.
    """
    
    request_body = {
        "contents": [{
            "parts": [{
                "text": legal_prompt
            }]
        }],
        "generationConfig": {
            "temperature": 0.1,
            "topP": 0.90,
            "topK": 40,
            "maxOutputTokens": 1024
        },
        "safetySettings": [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_LOW_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_LOW_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_LOW_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_LOW_AND_ABOVE"
            }
        ]
    }
    
    headers = {"Content-Type": "application/json"}
    
    response = requests.post(
        f"{endpoint}?key={GEMINI_API_KEY}",
        headers=headers,
        json=request_body,
        timeout=15
    )
    
    if not response.ok:
        error_details = f"API error {response.status_code}"
        try:
            error_data = response.json()
            if "error" in error_data:
                error_details += f": {error_data['error']['message']}"
        except:
            pass
        raise Exception(error_details)
    
    data = response.json()
    
    try:
        answer = data["candidates"][0]["content"]["parts"][0]["text"]
        
        # Add disclaimer if not present
        if "<i>Disclaimer:" not in answer:
            answer += """
            <br><br>
            <i>Disclaimer: This information is provided for educational purposes only and does not constitute legal advice. For specific legal issues, please consult a qualified lawyer.</i>
            """
        
        return answer
        
    except (KeyError, IndexError) as e:
        logger.error(f"Error parsing API response: {e}")
        raise Exception("Failed to parse API response")

@app.route('/test_api', methods=['GET'])
def test_api():
    """Simple endpoint to verify API connectivity"""
    try:
        response = get_legal_response("Explain the Right to Information Act briefly")
        return jsonify({
            "status": "API working", 
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "API error", 
            "error": str(e)
        })

@app.route('/topics', methods=['GET'])
def available_topics():
    """View available fallback topics"""
    topics = list(FALLBACK_RESPONSES.keys())
    return jsonify({"available_topics": topics})

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir)
        
        # Create index.html if missing
        index_path = os.path.join(templates_dir, 'index.html')
        if not os.path.exists(index_path):
            with open(index_path, 'w') as f:
                f.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Indian Law Assistant</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f5f7fa;
            padding-bottom: 40px;
        }
        .header {
            background-color: #1e3a8a;
            color: white;
            padding: 20px 0;
            margin-bottom: 30px;
            border-bottom: 5px solid #e2e8f0;
        }
        .query-container {
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            padding: 30px;
            margin-bottom: 30px;
        }
        .response-container {
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            padding: 30px;
            margin-top: 20px;
            min-height: 200px;
        }
        #response-box {
            padding: 20px;
            border-radius: 6px;
            background-color: #f8fafc;
            border-left: 4px solid #3b82f6;
        }
        .loader {
            display: none;
            text-align: center;
            margin: 20px 0;
        }
        .example-btn {
            margin: 5px;
            background-color: #e2e8f0;
            border: none;
            transition: all 0.2s;
        }
        .example-btn:hover {
            background-color: #cbd5e1;
        }
        .btn-primary {
            background-color: #2563eb;
            border: none;
        }
        .btn-primary:hover {
            background-color: #1d4ed8;
        }
    </style>
</head>
<body>
    <div class="header text-center">
        <div class="container">
            <h1>Indian Law Assistant</h1>
            <p>Get clear, accurate information on Indian laws and your legal rights</p>
        </div>
    </div>

    <div class="container">
        <div class="row justify-content-center">
            <div class="col-lg-8">
                <div class="query-container">
                    <h3 class="mb-4">Ask a Legal Question</h3>
                    <div class="mb-3">
                        <label for="query-input" class="form-label">What would you like to know about Indian law?</label>
                        <textarea class="form-control" id="query-input" rows="3" placeholder="Example: What are my rights if arrested?"></textarea>
                    </div>
                    <div class="d-grid gap-2">
                        <button class="btn btn-primary" id="submit-btn">Get Answer</button>
                    </div>
                    
                    <div class="mt-4 p-3 bg-light rounded">
                        <h5>Common Topics:</h5>
                        <div class="d-flex flex-wrap">
                            <button class="btn example-btn">Rights if arrested</button>
                            <button class="btn example-btn">How to file RTI</button>
                            <button class="btn example-btn">Fundamental rights</button>
                            <button class="btn example-btn">Consumer protection</button>
                            <button class="btn example-btn">Property laws</button>
                            <button class="btn example-btn">Divorce procedure</button>
                            <button class="btn example-btn">Reporting cyber crime</button>
                            <button class="btn example-btn">Labour rights</button>
                            <button class="btn example-btn">Criminal procedure</button>
                            <button class="btn example-btn">Family laws</button>
                        </div>
                    </div>
                </div>

                <div class="loader">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="mt-2">Finding legal information...</p>
                </div>

                <div class="response-container" id="response-section" style="display: none;">
                    <h3 class="mb-4">Legal Information</h3>
                    <div id="response-box"></div>
                </div>

                <div class="mt-4 text-center text-muted">
                    <small><strong>Disclaimer:</strong> This tool provides general information about Indian law for educational purposes only and does not constitute legal advice.</small>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const queryInput = document.getElementById('query-input');
            const submitBtn = document.getElementById('submit-btn');
            const responseSection = document.getElementById('response-section');
            const responseBox = document.getElementById('response-box');
            const loader = document.querySelector('.loader');
            const exampleBtns = document.querySelectorAll('.example-btn');

            exampleBtns.forEach(btn => {
                btn.addEventListener('click', function() {
                    queryInput.value = this.textContent;
                    submitBtn.click();
                });
            });

            submitBtn.addEventListener('click', async function() {
                const query = queryInput.value.trim();
                
                if (!query) {
                    alert('Please enter a legal question.');
                    return;
                }
                
                loader.style.display = 'block';
                responseSection.style.display = 'none';
                
                try {
                    const response = await fetch('/query', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ query: query })
                    });
                    
                    if (!response.ok) {
                        throw new Error('Server error: ' + response.status);
                    }
                    
                    const data = await response.json();
                    
                    loader.style.display = 'none';
                    responseSection.style.display = 'block';
                    responseBox.innerHTML = data.response;
                    
                    responseSection.scrollIntoView({ behavior: 'smooth' });
                    
                } catch (error) {
                    console.error('Error:', error);
                    loader.style.display = 'none';
                    responseSection.style.display = 'block';
                    responseBox.innerHTML = `
                        <div class="alert alert-danger">
                            <strong>Error:</strong> There was a problem processing your query. 
                            Please try again later.
                        </div>
                    `;
                }
            });
        });
    </script>
</body>
</html>""")
    
    app.run(debug=True, host='0.0.0.0', port=5000)