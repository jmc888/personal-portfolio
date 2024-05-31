import React, { useState } from 'react';
import axios from 'axios';

const QuestionAnsweringComponent = () => {
    const [question, setQuestion] = useState('');
    const [response, setResponse] = useState('');
    const [filename, setFilename] = useState('');
    const [loading, setLoading] = useState(false);

    const handleQuestionChange = (e) => {
        setQuestion(e.target.value);
    };  

    const handleQuestionSubmit = async () => {
        setLoading(true);
        setResponse('');
        setFilename('');

        try {
            const result = await axios.post('http://localhost:5000/query', { question });        
            setResponse(result.data.message);
            setFilename(result.data.filename);
        } catch (error) {
            setResponse('Error fetching response. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className='question-and-response' style={{ display: 'flex', justifyContent: 'space-between' }}>
            <div style={{ width: '30%' }}>
                <h3>Ask Your PDFs</h3>
                <textarea 
                    value={question}
                    onChange={handleQuestionChange}
                    placeholder="Ask a question about the uploaded documents..."
                    rows="4"
                    cols="60"
                /> 
                 <br/>
                <button onClick={handleQuestionSubmit}>Submit</button>
            </div>
            <div style={{ minWidth: '50%', width: '65%' }}>
                <h4>Response:</h4>
                {loading ? (<div>Loading...</div>) : (<p>{response} <br/><br/> {filename} </p>)}
            </div>
        </div>
    );
};

export default QuestionAnsweringComponent;