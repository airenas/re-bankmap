# customerRecognitions

1. externalDocumentNumber <- Statement_External_Document_No_
2. nereikia <- Cust_Posting_Date
3. nereikia <- Applied_Cust_Document_Date
4. recognizedAccountNumber <- Cust_Customer_No_
5. appliedDocumentNumber <- Applied_Cust_Document_No_

# vendorRecognitions

1. externalDocumentNumber <- Statement_External_Document_No_
2. nereikia <- Vend_Posting_Date
3. nereikia <- Applied_Vend_Document_Date
4. recognizedAccountNumber <- Vend_Vendor_No_
5. appliedDocumentNumber <- Applied_Vend_Document_No_

# bankAccountRecognitions
1. statementExternalDocumentNumber <- Statement_External_Document_No_
2. balAccountNumber <- Bal__Account_No_
3. balAccountType <- Bal__Account_Type

# bankStatementEntries
1. externalDocumentNumber <- External_Document_No_
2. bankAccountNumber <- Bank_Account_No_
3. description <- Description
4. messageToRecipient <- Message_to_Recipient
5. transactionType <- N_CdtDbtInd
6. amount <- N_Amt
7. operationDate <- N_BookDt_Dt
8. debtorIban <- N_ND_TD_RP_DbtrAcct_Id_IBAN
9. creditorIban <-N_ND_TD_RP_CdtrAcct_Id_IBAN
10. endToEndId<-- N_ND_TD_Refs_EndToEndId
11. accountCurrency <- Acct_Ccy
12. nereikia <- Recognized_Account_Type

# customerLedgerEntries
1. documentType <- Document_Type
1. customerNumber <- Customer_No_
1. documentNumber <- Document_No_
1. dueDate <- Due_Date
1. documentDate <- Document_Date
1. externalDocumentNumber <- External_Document_No_
1. amount <- Amount
1. currencyCode <- Currency_Code
1. closedAtDate <- ClosedAtDate
1. open <- Open
1. remainingAmount <- Remaining_Amount

# customerBankAccounts
1. customerNumber <- Customer_No_
1. bankAccountNumber <- Bank_Account_No_    IBAN ???  čia

# customers
1. number <- No_
1. name <- Name
1. applicationMethod <- Application_Method


# vendorLedgerEntries
1. documentType <- Document_Type
1. vendorNumber <- Vendor_No_
1. documentNumber <- Document_No_
1. dueDate <- Due_Date
1. documentDate <- Document_Date
1. externalDocumentNumber <- External_Document_No_
1. amount <- Amount
1. currencyCode <- Currency_Code
1. closedAtDate <- ClosedAtDate
1. isOpen <- Open
1. remainingAmount <- Remaining_Amount
   
# Vendor_Bank_Accounts
1. vendorNumber <- Vendor_No_
1. bankAccountNumber <- Bank_Account_No_

# Vendors
1. number <- No_
1. name <- Name
1. applicationMethod <- Application_Method

# GL_Accounts
1. number <- No_
1. searchName <- Search_Name

# Bank_Accounts
1. number <- No_
1. searchName <- Search_Name
1. iban <- IBAN
1. currencyCode <- Currency_Code

# Customer_Applications
1. documentNumber <- Document_No_
1. applicationCreatedDateTime <- Application_Created_Date
1. postingDate <- Posting_Date
1. - <- Customer
1. applicationAmount <- Application_Amount
1. remainingAmount <- Remaining_Amount

# Vendor_Applications
1. documentNumber Document_No_
1. applicationCreatedDateTime <- Application_Created_Date
1. postingDate <- Posting_Date
1. - <- Vendor
1. applicationAmount <- Application_Amount
1. remainingAmount <- Remaining_Amount

# bankStatementLines
1. externalDocumentNumber <- External_Document_No_
1. transactionType <- N_CdtDbtInd
1. creditorName <- N_ND_TD_RP_Cdtr_Nm
1. debtorName <- N_ND_TD_RP_Dbtr_Nm
1. transactionText <- N_ND_TD_RmtInf_Ustrd
1. statementChargesAmount <- N_Amt
1. operationDate <- N_BookDt_Dt
1. endToEndId <- N_ND_TD_Refs_EndToEndId
1. accountCurrency <- Acct_Ccy
1. bankAccountNumber <- Bank_Account_No_
2. endToEndId
