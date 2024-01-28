from beaker import *
from pyteal import *
from typing import Final

class FundIt:

    proposer: Final[GlobalStateValue] = GlobalStateValue(
        stack_type = abi.Byte,
        default = Bytes(""),
        descr="creator address of the campaign.",
    )

    title: Final[GlobalStateValue] = GlobalStateValue(
        stack_type= abi.String,
        default = str(""),
        descr="This is the title of the campaign.",
    )

    description: Final[GlobalStateValue] = GlobalStateValue(
        stack_type= abi.String,
        default = str(""),
        descr="This is the brief description of the campaign.",
    )

    deadline: Final[GlobalStateValue] = GlobalStateValue(
        stack_type= abi.Uint32,
        default = Int(0),
        descr="This is the deadline for this campaign",
    )

    goalAmount: Final[GlobalStateValue] = GlobalStateValue(
        stack_type=abi.Uint32,
        default = Int(0),
        descr="This is the goalAmount requested by the creator for this campaign.",
    )

    totalFunding: Final[GlobalStateValue] = GlobalStateValue(
        stack_type=abi.Uint32,
        default = Int(0),
        descr="This is the total amount funded till now.",
    )

app = Application("FundIt", state=FundIt)


@app.create
def create(
    _proposer: abi.Byte, 
    _title:abi.String, 
    _description: abi.String, 
    _deadline: abi.Uint32, 
    _goalAmount: abi.Uint32
    ) -> Expr:
    return Seq(
        Assert(app.state.deadline.get() == Int(0)),
        app.state.proposer.set(_proposer.get()),
        app.state.title.set(_title.get()),
        app.state.description.set(_description.get()),
        app.state.deadline.set(Global.latest_timestamp + (_deadline.get() * 86400)),
        app.state.goalAmount.set(_goalAmount.get()),
        app.state.totalFunding.set(Int(0)),
    )


@app.external(authorize=Authorize.only(Global.creator_address()))
def updateTitleAndDescription(
        _title: abi.String,
        _description: abi.String,
        *,
        _output: abi.String
     ) -> Expr:
    return Seq(
        app.state.title.set(_title),
        app.state.description.set(_description),
    )


@app.external(authorize=Authorize.anyone())
def fundToCampaign(_amount: abi.Uint32, *, _output: abi.Uint32) -> Expr:
    return Seq(
        Assert(app.state.deadline.get() > Global.latest_timestamp),
        app.state.totalFunding.set(app.state.totalFunding.get() + _amount.get()),
    )


@app.external(authorize=Authorize.only(Global.creator_address()))
def endCampaign(*, _output: abi.Bool) -> Expr:
    return Seq(
        Assert(app.state.totalFunding.get() >= app.state.goalAmount.get()),
        InnerTxnBuilder().begin(),
        InnerTxnBuilder().txnField(TxnField.receiver, app.state.proposer.get()),
        InnerTxnBuilder().txnField(TxnField.amount, app.state.totalFunding.get()),
        InnerTxnBuilder().submit(),
        _output.set(Int(1)),
    ) 
