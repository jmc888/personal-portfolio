import React from 'react';

const UploadedFiles = ({ files, onFileClick }) => {
    return (
        <div>
            <ul style={{  listStyleType: 'none',  paddingLeft: '5px', border: '1px solid #A9A9A9'  }}>
                {files.map((file, index) => (
                    <li key={index} style={{  padding: '5px' }}>
                        <a onClick={() => onFileClick(file)} href="#!">{file}</a>
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default UploadedFiles;
