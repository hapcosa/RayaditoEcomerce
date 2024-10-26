import {Fragment} from "react";
import {connect} from "react-redux";
import {CheckCircleIcon} from "@heroicons/react/24/outline";
function Alert({alert}) {
    const displayAlert = () => {
        if (alert !== null) {
            console.log(alert.alertType)
            const colour = alert.alertType
            console.log(colour)
        
            if(colour==='green'){
                return (
                    <>
                    <div className='rounded-md bg-green-50 p-4'>
                    <div className="flex">
                        <div className="flex-shrink-0">
                        <CheckCircleIcon className="h-5 w-5 text-green-400" />
                        </div>
                        <div className="ml-3">
                        <p className={`text-sm font-medium text-green-800`}>{alert.msg}</p>
                        </div>
                    </div>
                    </div>
                    </>
                )
            }else if(colour==='red'){
                return (
                    <>
                    <div className='rounded-md bg-red-50 p-4'>
                    <div className="flex">
                        <div className="flex-shrink-0">
                        <CheckCircleIcon className="h-5 w-5 text-red-400" />
                        </div>
                        <div className="ml-3">
                        <p className={`text-sm font-medium text-red-800`}>{alert.msg}</p>
                        </div>
                    </div>
                    </div>
                    </>
                )
                
            }
                
                
        } else {
            return (
                <Fragment></Fragment>
            )
        }
    }
    return (
        <Fragment> {
            displayAlert()
        } </Fragment>
    )
}

const mapStateToProps = state => ({alert: state.Alert.alert})
export default connect(mapStateToProps)(Alert)
