import React from 'react';
import UploadComponent from './components/UploadComponent';
import './styles.css';
import Chatbox from './components/Chatbox';

function Header() {
  return (
    <header className='header'> PDF Question Answering Chatbot
      </header>
  )
}

function App() {
  return (
    <div className="App" >
      <Header/>
      <div style={{ display: 'flex', justifyContent: 'space-between', flexDirection: 'column'}}>
        <div style={{ height: '80%', flex: '1', borderBottom: '2px solid gray'}}>
          <UploadComponent />
        </div>
        <div style={{ minHeight: '20%', flex: '1' }}>
          <Chatbox />
        </div>
      </div>
    </div>
  );
}

export default App;