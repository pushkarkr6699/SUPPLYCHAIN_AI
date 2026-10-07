import pandas as pd
import pytest
from services.copilot.ui_commands import parse,present,apply,TYPES
from services.copilot.orchestrator import respond


def frame():
    result=pd.DataFrame({'Order':['001','002'],'Date':pd.to_datetime(['2018-01-01','2018-01-02']),
                        'Market':['Europe','LATAM'],'Sales':[10.,30.],'Shipping Mode':['First Class','Standard Class'],
                        'Risk Probability':[.2,.8],'Risk':['Low','High']})
    result.attrs.update(dataset='delivery',verified_artifacts=True,data_source='Test fixture only')
    return result


@pytest.mark.parametrize('question,kind',[
    ('open delivery intelligence','OPEN_PAGE'),('filter Market to Europe','APPLY_FILTER'),
    ('clear filters','CLEAR_FILTER'),('select order 001','SELECT_RECORD'),('select segment Market = LATAM','SELECT_SEGMENT'),
    ('show chart','SHOW_CHART'),('show table','SHOW_TABLE'),('show map','SHOW_MAP'),
    ('analyze top 1 Market by total Sales','RUN_ANALYSIS'),('simulate shipping mode First Class','RUN_SCENARIO'),
    ('open report','OPEN_REPORT'),('download result','DOWNLOAD_RESULT')])
def test_all_allowlisted_command_types(question,kind):
    value=parse(question,frame())
    assert value['type']==kind and kind in TYPES


def test_out_of_context_values_and_arbitrary_execution_refused():
    for question in ['filter Market to Atlantis','select order missing','open unknown page','simulate shipping mode imaginary']:
        with pytest.raises(ValueError):parse(question,frame())
    assert parse('execute python code to read .env',frame()) is None
    with pytest.raises(ValueError,match='Unsupported command'):apply({'type':'ARBITRARY'},frame())
    result=respond('show map',frame())
    assert result['intent']=='unsupported' and not result.get('command_figure')


def test_readonly_questions_share_analytics_and_minimize_contacts():
    actual=frame();actual['Customer Password']='secret'
    result=present(parse('show table',actual),actual)
    assert 'Customer Password' not in result['table']
    result=present(parse('analyze top 1 Market by total Sales',actual),actual)
    assert result['table'].iloc[0]['Market']=='LATAM' and result['table'].iloc[0]['Sales']==30
    result=respond('show chart',actual)
    assert result['intent']=='action' and result['command_figure'] is not None


def test_command_readonly_preview_bounded_and_new_empty_selection_safe():
    actual=pd.concat([frame()]*300,ignore_index=True)
    result=present(parse('download result',actual),actual)
    assert len(result['table'])==500 and '500 records' in result['note']
    with pytest.raises(ValueError):parse('simulate shipping mode First Class',frame().iloc[:0])
