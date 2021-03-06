# -*- coding: utf-8 -*-
import logger
from crawler import NotifyParser
import re
from datetime import datetime
import user as u
import sys
import config


logger = logger.logger()

dates = '\d{4}-\d{2}-\d{2}|\d{2}.\d{2}.\d{4}|\d{2}.\d{2}.\d{2}|\d{1,2} \W* \d{4}'
def main():
    dba = None
    #get all outage from site
    ls = NotifyParser().get_all()
    if not ls:
        exit(0)
    logger.info(u'Чтение пользовательских настроек поиска')
    # usernotify = u.get_notify()
    usernotify = u.NotifyList()
    usernotify.load()
    #get all outage from db
    logger.info(u'Чтение уже созданных пользовательских уведомлений')
    # outage = u.get_useroutage()
    outage = u.OutageList()
    outage.load()
    #merge
    logger.info(u'создание списка уведомлений')
    # exist_list = {} # list of all notifies on site
    exist_list = u.OutageList()
    for notify in usernotify:
        for l in ls:
            if notify.city.lower() in l[0].lower() and (notify.street.lower() in l[1].lower() or (notify.street.lower() == u'все')):
                date_line = re.findall(dates, l[2].lower())
                if date_line[0]:
                    date_str = date_line[0]
                    for old, new in [(u'января', '01'), (u'февраля', '02'), (u'марта', '03'), (u'апреля', '04'), (u'мая', '05'), (u'июня', '06'), (u'июля', '07'), (u'августа', '08'), (u'сентября', '09'), (u'октября', '10'), (u'ноября', '11'), (u'декабря', '12')]:
                        if old in date_str:
                            date_str = date_str.replace(old, new)
                            break
                    try:
                        if '.' in date_str:
                            date_str = datetime.strptime(date_str, '%d.%m.%Y')
                        else:
                            date_str = datetime.strptime(date_str, '%d %m %Y')
                    except:
                        logger.error(date_str)
                        continue
                    o = u.Outage(0, notify.id, l[0], l[1], date_str, l[2], l[3])
                    exist_list.append(o)
    if not exist_list:
        logger.info(u'Не найдено уведомлений для заданных настроек поиска')
    if exist_list:
        if len(outage) == 0:
            logger.info(u'Добавление новых')
            for exist in exist_list:
                exist.save()
        else:
            #add
            logger.info(u'Добавление новых')
            for exist in exist_list:
                if outage.find(exist.usernotify_id, exist.city, exist.street, exist.date, exist.strdate, exist.reason) == 0 and exist.date.date() >= datetime.now().date():
                    exist.save()
            #del
            logger.info(u'Удаление старых')
            for out in outage:
                if exist_list.find(out.usernotify_id, out.city, out.street, out.date, out.strdate, out.reason) > 0:
                    out.delete()

    logger.info(u'Обновление завершено')


if __name__ == '__main__':
     if config.heroku_debug:
         logger.debug('remote debug')
         sys.path.append('/app/pycharm-debug.egg')
         import pydevd
         pydevd.settrace(config.server_debug, port=config.port_debug, stdoutToServer=True, stderrToServer=True)
     logger.info('Обновление событий')
     main()