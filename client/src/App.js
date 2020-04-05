import React, {useEffect, useRef, useState} from 'react';
import './App.css';
import TestList from "./TestList";
import EditTestDialog from "./EditTestDialog";
import LocustView from "./LocustView";

function useInterval(callback, delay) {
  const savedCallback = useRef();

  // Remember the latest callback.
  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);

  // Set up the interval.
  useEffect(() => {
    function tick() {
      savedCallback.current();
    }
    if (delay !== null) {
      let id = setInterval(tick, delay);
      return () => clearInterval(id);
    }
  }, [delay]);
}

export default () => {
  const [tests, setTests] = useState([]);
  const [test, setTest] = useState({});
  const [open, setOpen] = useState(false);
  const [openView, setOpenView] = useState(false);

  const loadTests = async () => {
    const result = await fetch('/tests');
    const json = await result.json();
    setTests(json);
  };

  const createTest = async (test) => {
    await fetch('/tests', {
      method: 'post',
      body: JSON.stringify(test)
    });
  };

  const updateTest = async (test) => {
    await fetch(`/tests/${test.id}`, {
      method: 'put',
      body: JSON.stringify(test)
    });
  };

  const deleteTest = async (test) => {
    await fetch(`/tests/${test.id}`, {
      method: 'delete'
    });
  };

  useEffect(() => {
    loadTests();
  }, []);

  useInterval(() => {
    loadTests();
  }, 1000);

  const handleView = async (test) => {
    setTest(test);
    setOpenView(true);
  };

  const handleStart = async (test) => {
    await fetch(`/tests/${test.id}/start`, {
      method: 'post'
    });
  };

  const handleStop = async (test) => {
    await fetch(`/tests/${test.id}/stop`, {
      method: 'post'
    });
  };

  const handleEdit = (test) => {
    setTest(test);
    setOpen(true);
  };

  const handleCancel = () => {
    setTest({});
    setOpen(false);
  };

  const handleCreate = async (test) => {
    setTest({});
    setOpen(false);
    await createTest(test);
    await loadTests();
  };

  const handleUpdate = async (test) => {
    setTest({});
    setOpen(false);
    await updateTest(test);
    await loadTests();
  };

  const handleDelete = async (test) => {
    setTest({});
    setOpen(false);
    await deleteTest(test);
    await loadTests();
  };

  const handleLocustViewClose = async () => {
    setTest({});
    setOpenView(false);
  };

  return (
    <div className="App">
      <TestList
        tests={tests}
        onView={handleView}
        onStart={handleStart}
        onStop={handleStop}
        onAdd={handleEdit}
        onEdit={handleEdit}
        onDelete={handleDelete}
      />
      <EditTestDialog
        open={open}
        test={test}
        onCancel={handleCancel}
        onCreate={handleCreate}
        onUpdate={handleUpdate}
      />
      <LocustView
        open={openView}
        test={test}
        onClose={handleLocustViewClose}
      />
    </div>
  );
};
