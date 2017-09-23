#!/usr/bin/env node

import * as HttpProvider from 'ethjs-provider-http';
import * as Eth from 'ethjs-query';
import * as EthContract from 'ethjs-contract';
import { ContractBlockchainData, ContractReceipt } from 'contract-deployment';

export class ContractDeployer {
    public async deployContract(ethjs: Eth, abi: any, bytecode: string, from: string, gas: number): Promise<ContractBlockchainData> {
        try {
            const contractBuilder = new EthContract(ethjs)(abi, bytecode, { from: from, gas: gas });
            const receiptAddress: string = await contractBuilder.new();
            const receipt: ContractReceipt = await ethjs.getTransactionReceipt(receiptAddress);
            return contractBuilder.at(receipt.contractAddress);
        } catch (error) {
            throw error;
        }
    }

    public async deployContracts(ethjs: Eth, contractJson: string, from: string, gas: number): Promise<ContractBlockchainData[]> {
        try {
            const contractFiles = JSON.parse(contractJson);
            let deployedContracts = [];
            for (let contractFileName in contractFiles) {
                for (let contractName in contractFiles[contractFileName]) {
                    // Filter out interface contracts, as the do not need to be deployed
                    if (contractFiles[contractFileName][contractName].evm.bytecode.object != '') {
                        // TODO: Change this to allow contracts to be deployed asynchronously; test to make sure name conflicts are avoided
                        deployedContracts[contractName] =  await this.deployContract(ethjs, contractFiles[contractFileName][contractName].abi, contractFiles[contractFileName][contractName].evm.bytecode.object, from, gas);
                    }
                }
            }
            return deployedContracts;
        } catch (error) {
            throw error;
        }
    }
}