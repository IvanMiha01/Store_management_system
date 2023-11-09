// SPDX-License-Identifier: GPL-3.0

pragma solidity ^0.8.2;

contract OrderContract{
    address payable owner;
    address customer;
    address payable courier;

    enum State {
        CREATED,
        PAYED,
        PENDING,
        COMPLETE
    }

    State state;

    uint price;

    modifier is_in_state(State required_state) {
        require(state == required_state, "Contract not in required state");
        _;
    }

    constructor (address _customer, uint _price) {
        owner = payable(msg.sender);
        customer = _customer;
        price = _price;

        state = State.CREATED;
    }

    function pay() external payable is_in_state(State.CREATED) {
        require(msg.sender == customer, "Only the customer can pay the order.");
        require(msg.value == price, "Incorrect payment amount.");

        state = State.PAYED;
    }

    function pick_up_order(address payable _courier) external is_in_state(State.PAYED) {
        require(msg.sender == owner, "Only the contract owner can bond a courier.");
        require(_courier != address(0), "Invalid courier address.");

        courier = _courier;
        
        state = State.PENDING;
    }

    function delivered() external is_in_state(State.PENDING) {
        require(msg.sender == customer, "Invalid customer account.");
        require(address(this).balance > 0, "Transfer not complete.");

        uint owner_cut = price * 80 / 100;
        uint courier_cut = price - owner_cut;

        owner.transfer(owner_cut);
        courier.transfer(courier_cut);
        
        state = State.COMPLETE;
    }
}
