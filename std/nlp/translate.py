
def cn2tw(text):
    import zhconv
    return zhconv.convert(text, 'zh-hant')
    
def tw2cn(text):
    import zhconv
    return zhconv.convert(text, 'zh-hans')

    