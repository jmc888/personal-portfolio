import React, { useState, useEffect, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSync } from '@fortawesome/free-solid-svg-icons';
import PDFPreview from './PDFPreview';
import UploadedFiles from './UploadedFiles';

const UploadComponent = () => {
    const [uploadedFiles, setUploadedFiles] = useState([]);
    const [selectedFile, setSelectedFile] = useState(null);

    useEffect(() => {
        fetchFiles();
    }, []);

    const fetchFiles = async () => {
        const response = await axios.get('http://localhost:5000/files');
        setUploadedFiles(response.data);
    };

    const onDrop = useCallback(acceptedFiles => {
        const formData = new FormData();
        formData.append('file', acceptedFiles[0]);

        axios.post('http://localhost:5000/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        }).then(() => {
            fetchFiles();
        });
    }, []);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop });

    const syncVectorStore = async () => {
        await axios.post('http://localhost:5000/sync_vector_store');
        alert('Vector store synced in PostgreSQL successfully!');
    };

    const handleFileClick = (filename) => {
        setSelectedFile(`http://localhost:5000/files/${filename}`);
    };

    return (
        <div className="upload-and-display" style={{ display: 'flex', justifyContent: 'space-between' }}>
            <div className="upload-section" style={{ width: '30%' }}>
                <h3>Upload and View PDFs</h3>
                <div {...getRootProps({ className: 'dropzone' })}>
                    <input {...getInputProps()} />
                    {
                        isDragActive ?
                            <p>Drop the files here ...</p> :
                            <p>Drag 'n' drop some files here, or click to select files</p>
                                                }
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <h4>Uploaded Files</h4>                
                    <button onClick={syncVectorStore}>
                        <FontAwesomeIcon icon={faSync} /> Sync with Vector Store
                    </button>
                </div>
                    <UploadedFiles files={uploadedFiles} onFileClick={handleFileClick} />
            </div>
            <div className="pdf-section" style={{ width: '60%' }}>
                {selectedFile && <PDFPreview selectedFile={selectedFile} />}
            </div>
        </div>
    );
};

export default UploadComponent;