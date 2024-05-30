import React from 'react';

const PDFPreview = ({ selectedFile }) => {
    return (
        <div>
            <h4>PDF Preview</h4>
            <iframe src={selectedFile} width="100%" height="800px" title="PDF Preview"></iframe>
        </div>
    );
};

export default PDFPreview;
