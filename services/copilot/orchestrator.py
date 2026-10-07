from services.copilot.intent import classify, unsafe_request
from services.copilot.context import snapshot
from services.copilot.response import build
from services.copilot.validation import validate_question


def respond(question, df, mode="Explore", selected_order=None, filters=None):
    question = validate_question(question)
    intent = classify(question, mode)
    result = build(intent, df, selected_order)
    if not unsafe_request(question):
        from services.copilot.ui_commands import parse,present
        try:
            command=parse(question,df,selected_order)
            if command:
                presentation=present(command,df)
                result.update(intent='action',title='Requested workspace action',narrative=presentation['note'],table=presentation['table'],chart=result['chart'].iloc[:0],command=command,command_figure=presentation['figure'])
                result['route']=command.get('route','scenarios' if command['type']=='RUN_SCENARIO' else 'copilot')
        except (ValueError,KeyError,TypeError) as error:
            result.update(intent='unsupported',title='Command needs a different selection',narrative=str(error))
    if unsafe_request(question):
        result.update(title="Request outside the analytics boundary", narrative="I can analyze approved dataset values. I cannot execute code or commands, access secret files, delete data, or modify models and thresholds.")
    result["evidence_context"] = snapshot(df, filters)
    if mode == "Simulate" and result['intent']!='action':
        result["route"] = "scenarios"
    elif mode == "Report" and intent != "unsupported" and result['intent']!='action':
        result["route"] = "reports"
    return result
