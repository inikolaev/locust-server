import TableContainer from "@material-ui/core/TableContainer";
import Paper from "@material-ui/core/Paper";
import Table from "@material-ui/core/Table";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import React from "react";
import TableCell from "@material-ui/core/TableCell";
import TableBody from "@material-ui/core/TableBody";
import Toolbar from "@material-ui/core/Toolbar";
import Typography from "@material-ui/core/Typography";
import Button from "@material-ui/core/Button";
import makeStyles from "@material-ui/core/styles/makeStyles";

const useStyles = makeStyles((theme) => ({
  root: {
    flexGrow: 1,
  },
  menuButton: {
    marginRight: theme.spacing(2),
  },
  title: {
    textAlign: 'left',
    flexGrow: 1,
  },
}));

export default (props) => {
  const { tests, onView, onStart, onStop, onAdd, onEdit, onDelete } = props;
  const classes = useStyles();

  return (
    <>
      <Toolbar>
        <Typography variant="h6" component="div" className={classes.title}>Tests</Typography>
        <Button variant="contained" color="primary" onClick={() => onAdd()} disableElevation>Add test</Button>
      </Toolbar>
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Host</TableCell>
              <TableCell align="right">Workers</TableCell>
              <TableCell>Status</TableCell>
              <TableCell></TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {tests.map((test) => (
              <TableRow key={test.id} hover={true}>
                <TableCell scope="row">
                  {test.name}
                </TableCell>
                <TableCell>{test.host}</TableCell>
                <TableCell align="right">{test.workers}</TableCell>
                <TableCell>{test.status}</TableCell>
                <TableCell align="right">
                  { test.status === 'running' && (
                    <Button onClick={() => onView(test)} disableElevation>View</Button>
                  )}
                  { test.status === 'stopped' && (
                      <Button onClick={() => onStart(test)} disableElevation>Start</Button>
                  )}
                  { test.status === 'running' && (
                      <Button onClick={() => onStop(test)} disableElevation>Stop</Button>
                  )}
                  <Button onClick={() => onEdit(test)} disableElevation>Edit</Button>
                  <Button onClick={() => onDelete(test)} disableElevation>Delete</Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </>
  );
};
