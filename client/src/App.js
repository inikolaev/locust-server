import React, {useEffect, useRef, useState} from 'react';
import './App.css';
import TestList from "./TestList";
import EditTestDialog from "./EditTestDialog";
import LocustView from "./LocustView";

const useInterval = (callback, delay) => {
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
};

const fetchWithTimeout = async (url, timeout, options) => {
  if (AbortController) {
    const controller = new AbortController();
    const signal = controller.signal;

    setTimeout(() => controller.abort(), timeout);

    return await fetch(url, {...options, signal});
  } else {
    const timeoutPromise = new Promise((_, reject) =>
      setTimeout(() => reject(new Error('timeout')), timeout)
    );

    const fetchPromise = fetch(url, options);
    return await Promise.race([fetchPromise, timeoutPromise]);
  }
};

export default () => {
  const [tests, setTests] = useState([]);
  const [test, setTest] = useState({});
  const [open, setOpen] = useState(false);
  const [openView, setOpenView] = useState(false);

  const loadTests = async () => {
    const result = await fetchWithTimeout('/tests', 5000);

    if (result.status === 200) {
      const json = await result.json();
      setTests(json);
    }
  };

  const createTest = async (test) => {
    await fetchWithTimeout('/tests', 5000, {
      method: 'post',
      body: JSON.stringify(test)
    });
  };

  const updateTest = async (test) => {
    await fetchWithTimeout(`/tests/${test.id}`, 5000, {
      method: 'put',
      body: JSON.stringify(test)
    });
  };

  const deleteTest = async (test) => {
    await fetchWithTimeout(`/tests/${test.id}`, 5000, {
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
    await fetchWithTimeout(`/tests/${test.id}/start`, 5000, {
      method: 'post'
    });
  };

  const handleStop = async (test) => {
    await fetchWithTimeout(`/tests/${test.id}/stop`, 5000, {
      method: 'post'
    });
  };

  const handleEdit = (test) => {
    setTest(test);
    setOpen(true);
  };

  const handleCopy = async (test) => {
    const copy = {...test, id: undefined, name: `${test.name} (copy)`};
    await createTest(copy);
    await loadTests();
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
        onCopy={handleCopy}
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
