import React from 'react';
import Button from "@material-ui/core/Button";


export default (props) => {
  const { open, test, onClose } = props;
  const handleClose= () => onClose && onClose();

  return open && (
    <div style={{position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, display: 'flex', flexDirection: 'column', background: '#0FF'}}>
        <div style={{padding: '10px'}}>
            <Button onClick={handleClose} color="primary">Close</Button>
        </div>
      <iframe src={`/proxy/${test.id}/`} style={{width: '100%', height: '100%', border: 0}}/>
    </div>
  );
};
