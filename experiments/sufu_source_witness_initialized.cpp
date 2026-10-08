// Independent JSON witness harness over the pinned upstream evaluation API.
// It does not synthesize, modify algorithms, or prove universal equivalence.
#include "istool/incre/io/incre_from_json.h"
#include "istool/incre/language/incre.h"
#include "istool/incre/analysis/incre_instru_runtime.h"
#include <json/json.h>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <regex>
#include "istool/incre/analysis/incre_instru_info.h"
#include "istool/sygus/theory/basic/clia/clia.h"

using namespace incre;

Data from_json(const Json::Value& v, int depth=0) {
    if (depth>100) throw std::runtime_error("JSON depth budget");
    if (v.isNull()) return Data(std::make_shared<VUnit>());
    if (v.isBool()) return Data(std::make_shared<VBool>(v.asBool()));
    if (v.isInt()) return Data(std::make_shared<VInt>(v.asInt()));
    if (v.isArray()) {
        DataList elements;
        for (const auto& e:v) elements.push_back(from_json(e,depth+1));
        return Data(std::make_shared<VTuple>(elements));
    }
    if (v.isObject() && v.getMemberNames().size()==2 && v.isMember("constructor") && v.isMember("payload") && v["constructor"].isString()) {
        return Data(std::make_shared<VInductive>(v["constructor"].asString(),from_json(v["payload"],depth+1)));
    }
    throw std::runtime_error("Not a signed32 first-order witness value");
}

Json::Value to_json(const Data& data) {
    auto* v=data.value.get();
    if (dynamic_cast<VUnit*>(v)) return Json::Value();
    if (auto* p=dynamic_cast<VInt*>(v)) return Json::Value(p->w);
    if (auto* p=dynamic_cast<VBool*>(v)) return Json::Value(p->w);
    if (auto* p=dynamic_cast<VTuple*>(v)) {
        Json::Value result(Json::arrayValue);
        for (const auto& e:p->elements) result.append(to_json(e));
        return result;
    }
    if (auto* p=dynamic_cast<VInductive*>(v)) {
        Json::Value result(Json::objectValue);
        result["constructor"]=p->name;result["payload"]=to_json(p->content);
        return result;
    }
    if (auto* p=dynamic_cast<VCompress*>(v)) return to_json(p->content);
    throw std::runtime_error("Output is not first-order data");
}

int main(int argc,char** argv) {
    if (argc!=4) {std::cerr<<"source.f input-only.json outputs.json\n";return 2;}
    try {
        Json::Value rows;Json::CharReaderBuilder reader;std::string error;
        std::ifstream input(argv[2]);
        if (!Json::parseFromStream(reader,input,&rows,&error) || !rows.isArray()) throw std::runtime_error("Invalid witness file: "+error);
        auto semantics=std::make_shared<Env>();
        prepareEnv(semantics.get());
        semantics->setConst(theory::clia::KINFName, BuildData(Int, 50000));
        auto program=parseFromF(argv[1],true);
        AddressHolder holder;EnvContext ctx(&holder);
        ctx.start=holder.extend(ctx.start,"al_inf",Data(std::make_shared<VInt>(100)));
        for (const auto& command:program->commands) envRun(command,&ctx);
        Json::Value results(Json::arrayValue);
        for (const auto& row:rows) {
            if (!row.isObject() || row.getMemberNames().size()!=3 || !row["entrypoint"].isString() || !row["inputs"].isObject() || !row["arguments"].isArray()) throw std::runtime_error("Witness must contain inputs only");
            std::string name=row["entrypoint"].asString();
            if (!std::regex_match(name,std::regex("[A-Za-z_][A-Za-z_0-9']*"))) throw std::runtime_error("Invalid entrypoint");
            std::unordered_map<std::string,Data> globals;
            for (const auto& field:row["inputs"].getMemberNames()) globals[field]=from_json(row["inputs"][field]);
            ctx.initGlobal(globals);
            Term term=std::make_shared<TmVar>(name);
            for (const auto& a:row["arguments"]) term=std::make_shared<TmApp>(term,std::make_shared<TmValue>(from_json(a)));
            int before=holder.address_list.size();
            try {
                auto value=envRun(term,ctx.start,&holder);
                results.append(to_json(value));
            } catch (const SemanticsError& e) {
                Json::Value error(Json::objectValue);error["native_semantics_error"]=true;
                results.append(error);
            }
            holder.recover(before);
        }
        Json::StreamWriterBuilder writer;writer["indentation"]="";
        std::ofstream output(argv[3],std::ios::out|std::ios::trunc);
        output<<Json::writeString(writer,results)<<"\n";
        std::cout<<"INPUT_ONLY_WITNESSES_EXECUTED "<<results.size()<<"\n";
        return 0;
    } catch(const std::exception& e) {std::cerr<<e.what()<<"\n";return 3;}
}
