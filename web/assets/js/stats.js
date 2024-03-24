// update statistics card
async function updateStat(reservoir) {
    await fetch(reservoir.actual_situation)
        .then(response => response.json())
        .then(data => {
            renderStat(reservoir, data);
        })
        .catch(error => {
            console.log('Error: ', error);
            renderStatError();
        });
};

// Render the statistics card
const renderStat = function(reservoir, data) {
    const actualDate = (new Date(data.date)).toLocaleDateString('ru', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });

    const statTitle = document.querySelector('#statTitle');
    const statTableOffsets = document.querySelector('#statTableOffsets');
    const statTableActual = document.querySelector('#statTableActual');

    statTitle.innerHTML = `<p class='lead mt-2 mb-0'><strong>${reservoir.name} водохранилище</strong></p>
                           <p class='text-muted mt-1'>по состоянию на ${actualDate}</p>`;

    statTableOffsets.innerHTML = `<td align='end' class='align-middle'><small class='text-muted mx-3'>Изменения за сутки</td>
                                  <td><small class='text-muted'>${data.level_offset} м</td>
                                  <td><small class='text-muted'>${data.inflow_offset} м\u00B3/с</td>
                                  <td><small class='text-muted'>${data.outflow_offset} м\u00B3/с</td>
                                  <td><small class='text-muted'>${data.spillway_offset} м\u00B3/с</td>`;

    statTableActual.innerHTML = `<td align='end' class='align-middle'><small class='text-muted mx-3'>Актуальные значения</td>
                                 <td><h5><span style='color:#ffc58c'>${data.level} м</td>
                                 <td><h5><span style='color:#ffa1b5'>${data.inflow} м\u00B3/с</td>
                                 <td><h5><span style='color:#86c7f3'>${data.outflow} м\u00B3/с</td>
                                 <td><h5><span style='color:#b894ff'>${data.spillway} м\u00B3/с</td>`;
};

// Render the statistics card error
const renderStatError = function(reservoir) {
    const statTitle = document.querySelector('#statTitle');
    const statTableOffsets = document.querySelector('#statTableOffsets');
    const statTableActual = document.querySelector('#statTableActual');

    statTitle.innerHTML = `<p class='lead mt-2 mb-0'><strong>${reservoir.name} водохранилище</strong></p>
                           <p class='text-muted mt-1'>Ошибка загрузки данных</p>`;

    statTableOffsets.innerHTML = `<td align='end' class='align-middle'><small class='text-muted mx-3'>Изменения за сутки</td>
                                  <td><small class='text-muted'>- м</td>
                                  <td><small class='text-muted'>- м\u00B3/с</td>
                                  <td><small class='text-muted'>- м\u00B3/с</td>
                                  <td><small class='text-muted'>- м\u00B3/с</td>`;

    statTableActual.innerHTML = `<td align='end' class='align-middle'><small class='text-muted mx-3'>Актуальные значения</td>
                                 <td><h5><span style='color:#ffc58c'>- м</td>
                                 <td><h5><span style='color:#ffa1b5'>- м\u00B3/с</td>
                                 <td><h5><span style='color:#86c7f3'>- м\u00B3/с</td>
                                 <td><h5><span style='color:#b894ff'>- м\u00B3/с</td>`;
};
