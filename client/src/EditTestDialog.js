import React, {useEffect, useRef, useState} from 'react';
import Button from '@material-ui/core/Button';
import TextField from '@material-ui/core/TextField';
import Dialog from '@material-ui/core/Dialog';
import DialogActions from '@material-ui/core/DialogActions';
import DialogContent from '@material-ui/core/DialogContent';
import DialogTitle from '@material-ui/core/DialogTitle';
import Editor, {monaco} from '@monaco-editor/react';

if (process.env.NODE_ENV === 'production') {
  monaco.config({paths: {vs: 'static/js/vs'}});
}

const defaultScript = [
  'from locust import HttpLocust, TaskSet, task',
  '',
  '',
  'class Tasks(TaskSet):',
  '    @task',
  '    def index(self):',
  '        self.client.get("/")',
  '',
  '',
  'class User(HttpLocust):',
  '    task_set = Tasks',
  ''
].join('\n');


export default (props) => {
  const { open, test={}, onCancel, onCreate, onUpdate } = props;

  const {
    id: testId = null,
    name: testName = '',
    host: testHost = '',
    workers: testWorkers = 4,
    script: testScript = defaultScript
  } = test;

  const [name, setName] = useState(testName);
  const [host, setHost] = useState(testHost);
  const [workers, setWorkers] = useState(testWorkers);
  const [script, setScript] = useState(testScript);
  const [nameError, setNameError] = useState(false);
  const [hostError, setHostError] = useState(false);
  const [workersError, setWorkersError] = useState(false);

  useEffect(() => {
    setName(testName);
    setHost(testHost);
    setWorkers(testWorkers);
    setScript(testScript);

    setNameError(false);
    setHostError(false);
    setWorkersError(false);
  }, [testName, testHost, testWorkers, testScript]);

  const reset = () => {
    setName('');
    setHost('');
    setWorkers(4);
    setScript(defaultScript);

    setNameError(false);
    setHostError(false);
    setWorkersError(false);
  };

  const handleCancel = () => {
    onCancel && onCancel();
    reset();
  };

  const handleCreate = () => {
    const hasErrors = name.trim().length === 0 || host.trim().length === 0 || workers <= 0;

    setNameError(name.trim().length === 0);
    setHostError(host.trim().length === 0);
    setWorkersError(workers <= 0);

    if (!hasErrors) {
      onCreate && onCreate({name, host, workers, script});
      reset();
    }
  };

  const handleUpdate = () => {
    const hasErrors = name.trim().length === 0 || host.trim().length === 0 || workers <= 0;

    setNameError(name.trim().length === 0);
    setHostError(host.trim().length === 0);
    setWorkersError(workers <= 0);

    if (!hasErrors) {
      onUpdate && onUpdate({id: testId, name, host, workers, script});
      reset();
    }
  };

  const editorRef = useRef();

  function handleEditorDidMount(_, editor) {
    editorRef.current = editor;
    editorRef.current.onDidChangeModelContent(ev => {
      setScript(editorRef.current.getValue());
    });
  }

  return (
    <Dialog open={open} onClose={handleCancel} maxWidth='lg' aria-labelledby="form-dialog-title">
      {testId ? (
        <DialogTitle id="form-dialog-title">Update Test</DialogTitle>
      ) : (
        <DialogTitle id="form-dialog-title">Create New Test</DialogTitle>
      )}

      <DialogContent>
        <TextField
          error={nameError}
          autoFocus
          margin="dense"
          id="name"
          label="Name"
          fullWidth
          value={name}
          required={true}
          onChange={(event) => setName(event.target.value)}
        />
        <TextField
          error={hostError}
          margin="dense"
          id="host"
          label="Host"
          fullWidth
          value={host}
          required={true}
          onChange={(event) => setHost(event.target.value)}
        />
        <TextField
          error={workersError}
          margin="dense"
          id="workers"
          label="Workers"
          type="number"
          fullWidth
          value={workers}
          required={true}
          onChange={(event) => setWorkers(event.target.valueAsNumber)}
        />
        <Editor
          height="400px"
          language="python"
          value={script}
          editorDidMount={handleEditorDidMount}
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onCancel}>
          Cancel
        </Button>
        {testId ? (
          <Button onClick={handleUpdate} color="primary">
            Update
          </Button>
        ) : (
          <Button onClick={handleCreate} color="primary">
            Create
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};
