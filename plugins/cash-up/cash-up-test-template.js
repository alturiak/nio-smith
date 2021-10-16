const realPayments = {
  Marius: 30,
  Andrea: 15,
  Niklas: 80,
}

// !register-users Marius 0,7; Andrea 0,15; Niklas 0,15;
const splitPercentage = {
  Marius: 0.7,
  Andrea: 0.15,
  Niklas: 0.15,
};

console.log({realPayments})
console.log({splitPercentage})

function logStage(stageNr){
  console.log("\n### Stage %s ###",stageNr)
}

let realPeople = Object.keys(realPayments);
let realValuesPaid = Object.values(realPayments);


// check for correct split percentage
const sumSplitPercentage = Object.values(splitPercentage).reduce((acc, curr) => curr + acc);
if(sumSplitPercentage !== 1 && sumSplitPercentage !== 100) {
  throw new Error("Split percentage must be 100% in total!!!")
}
console.log({sumSplitPercentage})
if(splitPercentage.length !== realPayments.length) {
  throw new Error("Split percentage must be the same length as ppl done payments!");
}

// 1. Sum up
logStage(1);
const sum = realValuesPaid.reduce((acc, curr) => curr + acc);
const mean = sum / realValuesPaid.length;
console.log({sum,mean})

// 2. Calculate parts
logStage(2);
// Summe Gesamt für jeden * mit seinem Faktor
const realPartsToPay = realPeople.map((person) => sum * splitPercentage[person]);
console.log({realPartsToPay})

// 3. 
logStage(3);
let payments = {}
const realDebts = realPeople.forEach((person) => {
  const key = person;
  const val = realPayments[person] - (sum * splitPercentage[person])
  payments[key] = val;
});
console.log({payments})


logStage("END");




function splitPayments(payments) {
  const people = Object.keys(payments);
  const valuesPaid = Object.values(payments);

  const sum = valuesPaid.reduce((acc, curr) => curr + acc);
  const mean = sum / people.length;

  //console.log({sum,mean})

  const sortedPeople = people.sort((personA, personB) => payments[personA] - payments[personB]);
  const sortedValuesPaid = sortedPeople.map((person) => payments[person] - mean);

  let i = 0;
  let j = sortedPeople.length - 1;
  let debt;

  while (i < j) {
    debt = Math.min(-(sortedValuesPaid[i]), sortedValuesPaid[j]);
    sortedValuesPaid[i] += debt;
    sortedValuesPaid[j] -= debt;

    console.log(`${sortedPeople[i]} owes ${sortedPeople[j]} $${debt}`);

    if (sortedValuesPaid[i] === 0) {
      i++;
    }

    if (sortedValuesPaid[j] === 0) {
      j--;
    }
  }
}

splitPayments(payments);

/*
  C owes B $400
  C owes D $100
  A owes D $200
*/