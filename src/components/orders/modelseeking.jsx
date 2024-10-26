import {React, useState} from 'react';
import { Modal, TextField, Button} from '@material-ui/core';
import {makeStyles} from '@material-ui/core'

const useStyles=makeStyles((theme) => ({
    model:{
        position: 'absolute',
        width: '400',
        backgroundColor: 'white',
        border: '2px solid white',
        boxShadow: theme.shadows[5],
        padding: '16px 32px 24px'

    }
}));

const delivery_timeline = ({ openClose}) =>{
    const styles = useStyles();
    return(
        <>
            <div className={styles.modal}>
                wena compare
                <Button onClick={openClose}></Button>
            </div>
        </>
    )

}
export default delivery_timeline;